import os
import logging
import uuid
import asyncio
import json
from typing import Dict, List, Optional, Any, AsyncGenerator, Union

import torch
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
import threading
import uvicorn
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_api")

# Enable debug logging
logger.setLevel(logging.DEBUG)

# --- Pydantic Models ---

class Message(BaseModel):
    role: str
    content: str

class GenerateRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[List[Message]] = None
    system_prompt: Optional[str] = None
    knowledge: Optional[str] = None
    max_tokens: int = Field(default=1024, ge=1, le=4096)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stream: bool = False
    session_id: Optional[str] = None

class GenerateResponse(BaseModel):
    text: str
    session_id: Optional[str] = None

class SessionRequest(BaseModel):
    system_prompt: Optional[str] = None
    knowledge: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    message: str

class OrderExtractionRequest(BaseModel):
    session_id: str
    api_key: str
    base_url: Optional[str] = "https://api.scaleway.ai/1487912f-76d4-4899-a8b3-1dbf08366f7c/v1"
    model: Optional[str] = "deepseek-r1-distill-llama-70b"

# --- LLM Service ---

class LLMService:
    """Manages LLM and sessions"""
    
    def __init__(self, model_name: str = "HuggingFaceTB/SmolLM2-1.7B-Instruct", device: str = None):
        """
        Initialize the LLM service
        
        Args:
            model_name: Model name/path
            device: Device to use (cuda, cpu, etc.)
        """
        # Determine device
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load model and tokenizer
        logger.info(f"Loading model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Set pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model with appropriate device mapping
        load_kwargs = {}
        if self.device != "cpu":
            load_kwargs["device_map"] = self.device
            
        self.model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
        self.model.eval()
        
        # Track sessions
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("LLM service initialized")
    
    def create_session(self, system_prompt: Optional[str] = None, knowledge: Optional[str] = None) -> str:
        """
        Create a new session
        
        Args:
            system_prompt: Optional system prompt
            knowledge: Optional knowledge context
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Initialize session data
        self.sessions[session_id] = {
            "conversation": [],
            "system_prompt": system_prompt,
            "knowledge": knowledge,
            "created": True
        }
        
        # Create combined system message if we have system prompt or knowledge
        if system_prompt or knowledge:
            system_content = ""
            
            if system_prompt:
                system_content += system_prompt
                
            if knowledge:
                if system_content:
                    system_content += "\n\n### KNOWLEDGE BASE ###\n" + knowledge
                else:
                    system_content = "### KNOWLEDGE BASE ###\n" + knowledge
            
            if system_content:
                # Add system message to conversation history
                self.sessions[session_id]["conversation"].append({
                    "role": "system",
                    "content": system_content
                })
                
                # Log for debugging
                logger.debug(f"Created session with system message: {system_content[:100]}...")
        
        logger.info(f"Created session: {session_id} with system prompt: {system_prompt is not None}, knowledge: {knowledge is not None}")
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to a session
        
        Args:
            session_id: Session ID
            role: Message role
            content: Message content
            
        Returns:
            Success flag
        """
        if session_id not in self.sessions:
            return False
            
        self.sessions[session_id]["conversation"].append({
            "role": role,
            "content": content
        })
        
        return True
    
    def get_conversation(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of messages
        """
        if session_id not in self.sessions:
            return []
            
        return self.sessions[session_id]["conversation"]
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear a session's conversation history
        
        Args:
            session_id: Session ID
            
        Returns:
            Success flag
        """
        if session_id not in self.sessions:
            return False
        
        # Get system prompt and knowledge
        system_prompt = self.sessions[session_id].get("system_prompt")
        knowledge = self.sessions[session_id].get("knowledge")
        
        # Reset conversation
        self.sessions[session_id]["conversation"] = []
        
        # Re-add system message if needed
        if system_prompt or knowledge:
            system_content = ""
            
            if system_prompt:
                system_content += system_prompt
                
            if knowledge:
                if system_content:
                    system_content += "\n\n### KNOWLEDGE BASE ###\n" + knowledge
                else:
                    system_content = "### KNOWLEDGE BASE ###\n" + knowledge
            
            if system_content:
                self.sessions[session_id]["conversation"].append({
                    "role": "system",
                    "content": system_content
                })
            
        return True
    
    async def generate_text(self, 
                            prompt: Optional[str] = None,
                            messages: Optional[List[Dict[str, str]]] = None,
                            system_prompt: Optional[str] = None,
                            knowledge: Optional[str] = None,
                            max_tokens: int = 1024,
                            temperature: float = 0.0,
                            top_p: float = 0.9,
                            session_id: Optional[str] = None,
                            stream: bool = False) -> AsyncGenerator[str, None]:
        """
        Generate text with the model
        
        Args:
            prompt: Text prompt (alternative to messages)
            messages: Conversation messages
            system_prompt: System prompt
            knowledge: Additional knowledge/context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling probability
            session_id: Optional session ID
            stream: Whether to stream response
            
        Yields:
            Generated text chunks (if streaming)
        """
        # Log the request parameters for debugging
        logger.debug(f"generate_text called with: prompt={prompt is not None}, "
                f"messages={messages is not None}, "
                f"system_prompt={system_prompt is not None}, "
                f"knowledge={knowledge is not None}, "
                f"session_id={session_id}")
        
        # Determine messages to use
        if messages is None:
            messages = []
            
            # First, get messages from session if available
            if session_id and session_id in self.sessions:
                messages = self.sessions[session_id]["conversation"].copy()
                
                # If knowledge is not provided but session has it, use that
                if knowledge is None and self.sessions[session_id]["knowledge"]:
                    knowledge = self.sessions[session_id]["knowledge"]
            
            # Check if we need to add system message (if not already in messages)
            has_system_message = any(m.get("role") == "system" for m in messages)
            if (system_prompt or knowledge) and not has_system_message:
                system_content = ""
                
                if system_prompt:
                    system_content += system_prompt
                    
                if knowledge:
                    if system_content:
                        system_content += "\n\n### KNOWLEDGE BASE ###\n" + knowledge
                    else:
                        system_content = "### KNOWLEDGE BASE ###\n" + knowledge
                
                if system_content:
                    messages.insert(0, {"role": "system", "content": system_content})
                    logger.debug(f"Added system message: {system_content[:100]}...")
            
            # Then add the user prompt if provided
            if prompt is not None:
                # First, save the user message to the session
                if session_id:
                    # Create session if it doesn't exist
                    if session_id not in self.sessions:
                        self.create_session(system_prompt, knowledge)
                    
                    # Add user message to session
                    self.add_message(session_id, "user", prompt)
                
                # Add to current generation messages
                messages.append({"role": "user", "content": prompt})
            
            # Validate we have something to work with
            if not messages:
                # No input provided
                raise ValueError("Either prompt, messages, or a valid session_id with conversation history must be provided")
        
        # Log the final messages for debugging
        logger.debug(f"Final messages for generation: {json.dumps([{'role': m.get('role'), 'content_length': len(m.get('content', ''))} for m in messages])}")
        
        # Create attention mask explicitly to prevent warnings
        input_ids = self.tokenizer.apply_chat_template(
            messages, 
            return_tensors="pt", 
            add_generation_prompt=True
        )
        attention_mask = torch.ones_like(input_ids)
        
        # Move to device
        if self.device != "cpu":
            input_ids = input_ids.to(self.device)
            attention_mask = attention_mask.to(self.device)
        
        # Create streamer
        streamer = TextIteratorStreamer(
            self.tokenizer, 
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        # Configure generation parameters
        gen_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "streamer": streamer,
            "max_new_tokens": max_tokens,
            "temperature": temperature,  # Avoid division by zero
            "top_p": top_p,
            "do_sample": temperature > 0,
        }
        
        # Start generation in a thread
        thread = threading.Thread(
            target=self._generate_thread, 
            args=(gen_kwargs,)
        )
        thread.start()
        
        # Accumulate full text
        full_text = ""
        
        # Stream tokens
        for new_text in streamer:
            full_text += new_text
            
            if stream:
                yield new_text
        
        # Save assistant response to session if provided
        if session_id:
            # Add assistant response
            self.add_message(session_id, "assistant", full_text)
        
        # Return full text if not streaming
        if not stream:
            yield full_text
    
    def _generate_thread(self, gen_kwargs):
        """Run text generation in a separate thread"""
        with torch.no_grad():
            self.model.generate(**gen_kwargs)

# --- FastAPI App ---

app = FastAPI(
    title="LLM API",
    description="API for text generation with LLM",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global LLM service instance
llm_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize LLM on startup"""
    global llm_service
    # Get model name from environment or use default
    model_name = os.environ.get("LLM_MODEL", "HuggingFaceTB/SmolLM2-1.7B-Instruct")
    device = os.environ.get("LLM_DEVICE", None)
    llm_service = LLMService(model_name=model_name, device=device)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "LLM API is running"}

@app.post("/generate", response_model=Union[GenerateResponse, None])
async def generate_text(request: GenerateRequest):
    """
    Generate text with the model
    
    Args:
        request: Generation request
        
    Returns:
        Generated text or streaming response
    """
    if llm_service is None:
        raise HTTPException(status_code=503, detail="LLM service not initialized")
    
    # Convert Pydantic models to dicts
    messages = None
    if request.messages:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Log request details for debugging
    logger.debug(f"Generate request: prompt={request.prompt is not None}, "
               f"messages={messages is not None}, "
               f"system_prompt={request.system_prompt is not None}, "
               f"knowledge={request.knowledge is not None}, "
               f"session_id={request.session_id}")
    
    try:
        # Handle streaming response
        if request.stream:
            async def generate_stream():
                async for chunk in llm_service.generate_text(
                    prompt=request.prompt,
                    messages=messages,
                    system_prompt=request.system_prompt,
                    knowledge=request.knowledge,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    session_id=request.session_id,
                    stream=True
                ):
                    # Format as Server-Sent Event
                    yield f"data: {chunk}\n\n"
                
                # Send end marker
                yield f"data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # Non-streaming response
            result = ""
            async for text in llm_service.generate_text(
                prompt=request.prompt,
                messages=messages,
                system_prompt=request.system_prompt,
                knowledge=request.knowledge,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                session_id=request.session_id,
                stream=False
            ):
                result = text
                
            return {"text": result, "session_id": request.session_id}
            
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract_order")
async def extract_order(request: OrderExtractionRequest):
    """
    Extract order information from conversation using DeepSeek API
    
    Args:
        request: Order extraction request with session ID and API key
        
    Returns:
        Extracted order information as JSON
    """
    if llm_service is None:
        raise HTTPException(status_code=503, detail="LLM service not initialized")
        
    # Get conversation history
    conversation = llm_service.get_conversation(request.session_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation for session {request.session_id} not found")
    
    # Prepare the conversation for DeepSeek
    formatted_conversation = []
    for msg in conversation:
        formatted_conversation.append({
            "role": msg.get("role"),
            "content": msg.get("content", "")
        })
    
    # Add the instruction message to extract order information
    extraction_prompt = """
    Based on the conversation above, extract all order information into a structured JSON format. Include:
    
    1. Customer information (name and delivery address)
    2. All ordered items with their names, quantities, and prices
    3. The total order amount
    
    Return ONLY valid JSON in this format:
    {
      "customer": {
        "name": "Customer name or null if unknown",
        "address": "Delivery address or null if not provided"
      },
      "items": [
        {"product_name": "Product Name", "quantity": 1, "price": 10.99},
        {"product_name": "Another Product", "quantity": 2, "price": 5.99}
      ],
    }
    
    Do not include any text outside the JSON. If no order is detected, return an empty items array and null values.
    """
    
    formatted_conversation.append({
        "role": "user",
        "content": extraction_prompt
    })
    
    try:
        # Call DeepSeek API
        client = OpenAI(
            base_url=request.base_url,
            api_key=request.api_key
        )
        
        response = client.chat.completions.create(
            model=request.model,
            messages=formatted_conversation,
            max_tokens=1024,
            temperature=0.1,  # Low temperature for more deterministic output
            top_p=0.95
        )
        
        # Extract the response text
        result_text = response.choices[0].message.content
        
        # Try to parse JSON
        try:
            # Remove any leading/trailing non-JSON text
            import re
            json_match = re.search(r'({.*})', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
                
            # Parse JSON
            order_data = json.loads(result_text)
            return order_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepSeek response as JSON: {e}")
            logger.debug(f"DeepSeek response: {result_text}")
            raise HTTPException(status_code=422, detail=f"DeepSeek response is not valid JSON: {e}")
            
    except Exception as e:
        logger.error(f"Error calling DeepSeek API: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling DeepSeek API: {e}")

@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """
    Create a new session
    
    Args:
        request: Session configuration
        
    Returns:
        Session ID
    """
    if llm_service is None:
        raise HTTPException(status_code=503, detail="LLM service not initialized")
    
    # Log request details
    logger.debug(f"Create session request: system_prompt={request.system_prompt is not None}, "
               f"knowledge={request.knowledge is not None}")
    
    if request.system_prompt:
        logger.debug(f"System prompt preview: {request.system_prompt[:100]}...")
        
    if request.knowledge:
        logger.debug(f"Knowledge preview: {request.knowledge[:100]}...")
        
    session_id = llm_service.create_session(
        system_prompt=request.system_prompt,
        knowledge=request.knowledge
    )
    
    return {"session_id": session_id, "message": "Session created"}

@app.post("/sessions/{session_id}/clear", response_model=SessionResponse)
async def clear_session(session_id: str):
    """
    Clear a session's conversation history
    
    Args:
        session_id: Session ID
        
    Returns:
        Status message
    """
    if llm_service is None:
        raise HTTPException(status_code=503, detail="LLM service not initialized")
        
    success = llm_service.clear_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
    return {"session_id": session_id, "message": "Session cleared"}

@app.get("/sessions/{session_id}/conversation")
async def get_conversation(session_id: str):
    """
    Get conversation history for a session
    
    Args:
        session_id: Session ID
        
    Returns:
        Conversation history
    """
    if llm_service is None:
        raise HTTPException(status_code=503, detail="LLM service not initialized")
        
    conversation = llm_service.get_conversation(session_id)
    
    if not conversation and session_id not in llm_service.sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
    return {"session_id": session_id, "conversation": conversation}

# --- Main entry point ---

def main():
    """Run the server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--model", type=str, default="HuggingFaceTB/SmolLM2-1.7B-Instruct", help="Model to use")
    parser.add_argument("--device", type=str, default=None, help="Device to use (cuda, cpu)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger("llm_api").setLevel(logging.DEBUG)
    
    # Set environment variables for the app
    os.environ["LLM_MODEL"] = args.model
    if args.device:
        os.environ["LLM_DEVICE"] = args.device
    
    # Run the app
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()