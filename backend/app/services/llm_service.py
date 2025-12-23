import os
import json
import requests
from typing import Dict, Any, Optional, List

class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(self, provider="huggingface", api_key=None):
        """
        Initialize the LLM service.
        
        Args:
            provider: The LLM provider to use ("huggingface", "openai", "anthropic")
            api_key: API key for the provider (if None, will look for environment variable)
        """
        self.provider = provider
        self.api_key = api_key
        
        # Set up provider-specific configuration
        if provider == "huggingface":
            self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
            self.api_url = "https://api-inference.huggingface.co/models/"
            self.model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
        elif provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        elif provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a response from the LLM using the provided prompt.
        
        Args:
            prompt: The formatted prompt to send to the LLM
            
        Returns:
            The generated response as a string
        """
        
        if self.provider == "huggingface":
            return await self._generate_huggingface(prompt)
        elif self.provider == "openai":
            return await self._generate_openai(prompt)
        elif self.provider == "anthropic":
            return await self._generate_anthropic(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _generate_huggingface(self, prompt: str) -> str:
        """Generate a response using Hugging Face API."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Format prompt specifically for Mistral Instruct models
            if "mistral" in self.model.lower():
                formatted_prompt = {
                    "inputs": f"<s>[INST] {prompt} [/INST]",
                    "parameters": {
                        "max_new_tokens": 1024,
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "return_full_text": False
                    }
                }
            else:
                # Generic format for other models
                formatted_prompt = {
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 1024,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                }
            
            response = requests.post(
                f"{self.api_url}{self.model}",
                headers=headers,
                json=formatted_prompt
            )
            
            if response.status_code != 200:
                print(f"Error from Hugging Face API: {response.text}")
                return f"Error: {response.status_code}"
            
            result = response.json()
            
            # Handle different response formats from Hugging Face
            if isinstance(result, list) and len(result) > 0:
                if "generated_text" in result[0]:
                    return result[0]["generated_text"]
                return str(result[0])
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            else:
                return str(result)
                
        except Exception as e:
            print(f"Error calling Hugging Face API: {e}")
            return f"Error: {str(e)}"
    
    async def _generate_openai(self, prompt: str) -> str:
        """Generate a response using OpenAI API."""
        try:
            # This is a placeholder - you'll need to install the OpenAI package
            # and implement this method when you switch to OpenAI
            import openai
            openai.api_key = self.api_key
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful data analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return f"Error: {str(e)}"
    
    async def _generate_anthropic(self, prompt: str) -> str:
        """Generate a response using Anthropic API."""
        try:
            # This is a placeholder - you'll need to install the Anthropic package
            # and implement this method when you switch to Anthropic
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.1,
                system="You are a helpful data analysis assistant.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"Error calling Anthropic API: {e}")
            return f"Error: {str(e)}"
    
    def change_provider(self, provider: str, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Change the LLM provider.
        
        Args:
            provider: The new provider to use
            api_key: API key for the new provider
            model: Model to use with the new provider
        """
        self.provider = provider
        
        if api_key:
            self.api_key = api_key
        
        if provider == "huggingface":
            self.api_key = self.api_key or os.getenv("HUGGINGFACE_API_KEY")
            self.api_url = "https://api-inference.huggingface.co/models/"
            self.model = model or os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
        elif provider == "openai":
            self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        elif provider == "anthropic":
            self.api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
