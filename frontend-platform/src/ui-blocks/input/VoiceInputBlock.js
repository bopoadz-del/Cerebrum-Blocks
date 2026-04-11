import { UIBlock, registerBlock } from '../../blocks/UIBlock.js';

// VoiceInputBlock - Handles voice recording and STT
class VoiceInputBlock extends UIBlock {
  constructor(config = {}) {
    super({
      name: 'voice_input',
      layer: 2,
      tags: ['input', 'voice', 'audio'],
      requires: ['api']
    });
    this.api = config.api;
    this.mediaRecorder = null;
    this.chunks = [];
    this.isRecording = false;
  }

  async process(action, params = {}) {
    switch (action) {
      case 'start':
        return this.startRecording();
      case 'stop':
        return this.stopRecording();
      case 'transcribe':
        return this.transcribeFile(params.file);
      default:
        throw new Error(`Unknown voice action: ${action}`);
    }
  }

  async startRecording() {
    if (this.isRecording) {
      throw new Error('Already recording');
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream);
      this.chunks = [];

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          this.chunks.push(e.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        this.isRecording = false;
        this.emit('recording:stop');
      };

      this.mediaRecorder.start();
      this.isRecording = true;

      this.emit('recording:start');
      
      return { status: 'recording' };

    } catch (error) {
      this.emit('recording:error', { error: error.message });
      throw error;
    }
  }

  async stopRecording() {
    if (!this.isRecording || !this.mediaRecorder) {
      throw new Error('Not recording');
    }

    return new Promise((resolve, reject) => {
      this.mediaRecorder.onstop = async () => {
        try {
          this.isRecording = false;
          
          // Create audio file
          const audioBlob = new Blob(this.chunks, { type: 'audio/webm' });
          const file = new File([audioBlob], 'voice.webm', { type: 'audio/webm' });
          
          this.emit('recording:stop', { duration: this.mediaRecorder.duration });
          
          // Transcribe
          const result = await this.transcribeFile(file);
          resolve(result);
          
        } catch (error) {
          this.emit('recording:error', { error: error.message });
          reject(error);
        }
      };

      this.mediaRecorder.stop();
      
      // Stop all tracks
      this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
    });
  }

  async transcribeFile(file) {
    this.emit('transcribe:start', { file: file.name });

    try {
      // 1. Upload audio file
      const upload = await this.api.uploadFile(file);

      // 2. Call voice block for STT
      const result = await this.api.executeBlock('voice', {
        action: 'stt',
        audio_url: upload.url,
        provider: 'whisper',
        language: 'auto'
      });

      const transcription = result.text || result.transcription || result;

      this.emit('transcribe:complete', { 
        text: transcription,
        confidence: result.confidence 
      });

      return {
        text: transcription,
        confidence: result.confidence,
        url: upload.url
      };

    } catch (error) {
      this.emit('transcribe:error', { error: error.message });
      throw error;
    }
  }

  isRecording() {
    return this.isRecording;
  }
}

registerBlock('voice_input', VoiceInputBlock);
export default VoiceInputBlock;
