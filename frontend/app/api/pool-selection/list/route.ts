import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const datasetId = searchParams.get('dataset_id');
    
    console.log(`Proxying list request to backend with dataset_id: ${datasetId}`);
    
    // Get the authorization header from the incoming request
    const authHeader = req.headers.get('authorization');
    if (!authHeader) {
      console.error('No authorization header found in request');
      return NextResponse.json(
        { error: 'Authorization header missing' },
        { status: 401 }
      );
    }
    
    console.log('Forwarding list request with auth header');
    const response = await fetch(`http://localhost:8000/api/pool-selection/list?dataset_id=${datasetId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
    });
    
    if (!response.ok) {
      console.error(`Backend returned error: ${response.status} ${response.statusText}`);
      return NextResponse.json(
        { error: `Backend returned ${response.status}: ${response.statusText}` }, 
        { status: response.status }
      );
    }
    
    const data = await response.json();
    console.log(`Successfully received list of ${data.pools?.length || 0} saved pools`);
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in list proxy route:', error);
    return NextResponse.json(
      { error: 'Internal server error in proxy', details: String(error) }, 
      { status: 500 }
    );
  }
}
