# Conversational Voice Agents Platform

A comprehensive platform for building, deploying, and managing intelligent voice agents that can handle natural conversations with customers through voice interfaces. Perfect for automating phone-based customer interactions without requiring technical expertise.

## Demo Video

<video src="https://github.com/FILALIHicham/Conversational-voice-agent-platform/Demo.mp4" controls></video>

## Project Overview

This platform enables businesses to create voice agents that can engage in natural, real-time conversations with customers. The system combines three key AI technologies in a cascade architecture:

1. **Automatic Speech Recognition (ASR)** - Converts spoken language to text
2. **Large Language Model (LLM)** - Processes text and generates contextual responses
3. **Text-to-Speech (TTS)** - Converts text responses to natural-sounding speech

The platform handles the complete pipeline from voice input to voice output with low-latency streaming capabilities and proper turn-taking between users and agents.

## Technical Implementation

### Frontend
- **React** with **Tailwind CSS** for a responsive, modern UI
- Web interface for configuring and deploying voice agents

### Backend
- **Flask** 3-tier architecture:
  - Models layer (domain objects)
  - Controllers layer (API endpoints)
  - DAO layer (data access)
- **JWT authentication** with 10-minute refresh tokens
- Modular service design with clear separation of concerns

### Database
- **MySQL** database
- **SQLAlchemy** ORM for database interactions
- Storage for agent configurations, user data, and conversation history

### Speech Recognition (ASR)
- **NVIDIA NeMo FastConformer** (`stt_en_fastconformer_hybrid_large_streaming_multi`)
- Custom **energy-based VAD** (Voice Activity Detection) with state machine for accurate speech segmentation
- Configurable VAD parameters (threshold, speech padding, minimum duration)
- WebSocket-based streaming interface for real-time transcription

### Language Processing (LLM)
- **SmolLM2-1.7B-Instruct** model for response generation
- Context management and conversation history
- Knowledge injection through prompt engineering
- System prompt customization for agent behavior and domain knowledge
- Streaming text generation for responsive interactions

### Speech Synthesis (TTS)
- **Kokoro 82M** TTS model for natural-sounding speech
- **Parallel chunking approach** - Splits LLM response in real-time by punctuation boundaries
- Multiple TTS processes run in parallel to reduce end-to-end latency
- Sentence-level streaming for natural prosody

### Post-Processing
- **DeepSeek API** integration for structured information extraction
- Processes conversation transcripts to extract customer data (name, address)
- Identifies order details (items, quantities, prices) for database storage
- Compensates for limitations in smaller LLMs that struggle with structured outputs

## Architecture

The platform follows a modular, service-oriented architecture:

```
voice-agent-platform/
├── core/                        # Core AI services
│   ├── asr_api.py               # Speech recognition with VAD
│   ├── llm_api.py               # Language model service
│   └── tts_api.py               # Text-to-speech with parallel processing
├── agents/                      # Agent orchestration
│   ├── agent.py                 # Voice agent implementation
│   ├── factory.py               # Configuration and lifecycle management
│   └── configs/                 # YAML configuration files
├── web/
│   ├── backend/                 # Flask application
│   │   ├── app.py               # Main application entry point
│   │   ├── models/              # Domain objects
│   │   ├── controllers/         # API endpoints and routing
│   │   ├── dao/                 # Data access layer
│   │   └── extensions.py        # Flask extensions
└── └── frontend/                # React + Tailwind application
```

## Key Features

### Low-Latency Conversation
- Streaming ASR with real-time transcription
- Streaming LLM response generation
- Parallel TTS processing of sentence chunks
- WebSocket-based communication for minimal delay

### Voice Activity Detection
- Energy-based speech detection
- Configurable parameters for different environments
- State machine for robust utterance boundary detection
- Automatic speech/silence classification

### Knowledge Injection
- System prompt customization for domain knowledge
- Context-aware responses based on conversation history
- Integration with business data for personalized interactions

### Order Processing
- DeepSeek API integration for structured data extraction
- Real-time parsing of customer information
- Automatic extraction of order details
- Database storage of processed orders

## MLOps Integration

This project integrates with the MLOps pipeline available at [MLOps_Mini_Project](https://github.com/FILALIHicham/MLOps_Mini_Project). The MLOps integration provides:

- Recommendation engine based on order history
- Implicit ratings generation (1-5) based on purchase patterns
- Context-aware recommendations (time of day, day of week)
- Singular Value Decomposition (SVD) for personalized recommendations
- Popularity-based fallback for new customers
- MLOps lifecycle management (training, testing, deployment)

---

## Acknowledgments

- NVIDIA NeMo team for the speech recognition models
- Hugging Face for the SmolLM2 model
- Kokoro TTS developers for the speech synthesis engine