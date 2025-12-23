import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const searchParams = req.nextUrl.searchParams;
    const datasetId = searchParams.get('dataset_id');
    
    console.log(`Proxying request to backend with dataset_id: ${datasetId}`);
    
    // Get the authorization header from the incoming request
    const authHeader = req.headers.get('authorization');
    if (!authHeader) {
      console.error('No authorization header found in request');
      return NextResponse.json(
        { error: 'Authorization header missing' },
        { status: 401 }
      );
    }
    
    console.log('Forwarding request with auth header');
    const response = await fetch(`http://localhost:8000/api/pool-selection/filter?dataset_id=${datasetId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      console.error(`Backend returned error: ${response.status} ${response.statusText}`);
      return NextResponse.json(
        { error: `Backend returned ${response.status}: ${response.statusText}` }, 
        { status: response.status }
      );
    }
    
    const data = await response.json();
    console.log(`Successfully received response from backend with ${data.records?.length || 0} records`);
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in pool-selection proxy route:', error);
    return NextResponse.json(
      { error: 'Internal server error in proxy', details: String(error) }, 
      { status: 500 }
    );
  }
}
