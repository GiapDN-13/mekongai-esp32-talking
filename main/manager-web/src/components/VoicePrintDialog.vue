<template>
  <el-dialog :title="title" :visible.sync="visible" width="560px" class="param-dialog-wrapper" :append-to-body="true"
    :close-on-click-modal="false" :key="dialogKey" custom-class="custom-param-dialog" :show-close="false">
    <div class="dialog-container">
      <div class="dialog-header">
        <h2 class="dialog-title">{{ title }}</h2>
        <button class="custom-close-btn" @click="cancel">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 1L1 13M1 1L13 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </button>
      </div>

      <el-form :model="form" :rules="rules" ref="form" label-width="auto" label-position="left" class="param-form">
        <!-- Audio source tabs -->
        <el-form-item :label="$t('voicePrintDialog.voicePrintVector')" prop="audioId" class="form-item">
          <div class="audio-source-tabs">
            <div class="tab-buttons">
              <button type="button" :class="['tab-btn', { active: audioSourceTab === 'history' }]"
                @click="audioSourceTab = 'history'">
                <i class="el-icon-chat-dot-round"></i> {{ $t('voicePrintDialog.fromHistory') || 'Lịch sử chat' }}
              </button>
              <button type="button" :class="['tab-btn', { active: audioSourceTab === 'record' }]"
                @click="audioSourceTab = 'record'">
                <i class="el-icon-microphone"></i> {{ $t('voicePrintDialog.fromMicrophone') || 'Thu âm' }}
              </button>
              <button type="button" :class="['tab-btn', { active: audioSourceTab === 'upload' }]"
                @click="audioSourceTab = 'upload'">
                <i class="el-icon-upload2"></i> {{ $t('voicePrintDialog.fromFile') || 'Tải file' }}
              </button>
            </div>

            <!-- Tab: History -->
            <div v-show="audioSourceTab === 'history'" class="tab-content">
              <el-select v-model="form.audioId" :placeholder="$t('voicePrintDialog.selectVoiceMessage')"
                class="custom-select">
                <el-option v-for="item in valueTypeOptions" :key="item.audioId" :label="item.content"
                  :value="item.audioId">
                  <span style="float: left">{{ item.content }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">
                    <i :class="getAudioIconClass(item.audioId)" @click.stop="playAudio(item.audioId)"
                      class="audio-icon"></i>
                  </span>
                </el-option>
              </el-select>
              <div v-if="valueTypeOptions.length === 0" class="empty-hint">
                {{ $t('voicePrintDialog.noHistoryAudio') || 'Chưa có lịch sử hội thoại. Hãy thu âm hoặc tải file.' }}
              </div>
            </div>

            <!-- Tab: Record from microphone -->
            <div v-show="audioSourceTab === 'record'" class="tab-content">
              <div class="record-area">
                <div class="record-controls">
                  <button type="button" class="record-btn" :class="{ recording: isRecording }"
                    @click="toggleRecording">
                    <i :class="isRecording ? 'el-icon-video-pause' : 'el-icon-microphone'"></i>
                    {{ isRecording ? ($t('voicePrintDialog.stopRecording') || 'Dừng') :
                      ($t('voicePrintDialog.startRecording') || 'Bắt đầu thu âm') }}
                  </button>
                  <span v-if="isRecording" class="recording-timer">{{ formatTime(recordingTime) }}</span>
                </div>
                <div v-if="isRecording" class="recording-indicator">
                  <span class="pulse-dot"></span>
                  {{ $t('voicePrintDialog.recordingHint') || 'Đang thu âm... Hãy nói rõ ràng 5-20 giây' }}
                </div>
                <div v-if="recordedBlob && !isRecording" class="recorded-preview">
                  <div class="preview-row">
                    <button type="button" class="play-btn" @click="playRecorded">
                      <i :class="isPlayingRecorded ? 'el-icon-video-pause' : 'el-icon-video-play'"></i>
                    </button>
                    <span class="recorded-info">{{ $t('voicePrintDialog.recordedDuration') || 'Đã thu' }}:
                      {{ formatTime(recordedDuration) }}</span>
                    <button type="button" class="clear-btn" @click="clearRecording">
                      <i class="el-icon-delete"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab: Upload file -->
            <div v-show="audioSourceTab === 'upload'" class="tab-content">
              <div class="upload-area">
                <el-upload ref="audioUpload" action="#" :auto-upload="false" :on-change="handleFileChange"
                  :show-file-list="false" accept="audio/*,.wav,.mp3,.ogg,.webm">
                  <div class="upload-box">
                    <i class="el-icon-upload"></i>
                    <span>{{ uploadedFileName || ($t('voicePrintDialog.clickToUpload') || 'Chọn file WAV/MP3 (5-30 giây)') }}</span>
                  </div>
                </el-upload>
                <div v-if="uploadedBlob" class="recorded-preview">
                  <div class="preview-row">
                    <button type="button" class="play-btn" @click="playUploaded">
                      <i :class="isPlayingUploaded ? 'el-icon-video-pause' : 'el-icon-video-play'"></i>
                    </button>
                    <span class="recorded-info">{{ uploadedFileName }}</span>
                    <button type="button" class="clear-btn" @click="clearUpload">
                      <i class="el-icon-delete"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-form-item>

        <el-form-item :label="$t('voicePrintDialog.name')" prop="sourceName" class="form-item">
          <el-input v-model="form.sourceName" :placeholder="$t('voicePrintDialog.enterName')"
            class="custom-input"></el-input>
        </el-form-item>

        <el-form-item :label="$t('voicePrintDialog.description')" prop="introduce" class="form-item remark-item">
          <el-input type="textarea" v-model="form.introduce"
            :placeholder="$t('voicePrintDialog.enterDescription')" :rows="3" class="custom-textarea" maxlength="100"
            show-word-limit></el-input>
        </el-form-item>
      </el-form>

      <div class="dialog-footer">
        <el-button type="primary" @click="submit" class="save-btn" :loading="saving" :disabled="saving">
          {{ $t('voicePrintDialog.save') }}
        </el-button>
        <el-button @click="cancel" class="cancel-btn">
          {{ $t('voicePrintDialog.cancel') }}
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script>
import api from '@/apis/api';
import { getServiceUrl } from '@/apis/serviceUrl';

export default {
  props: {
    title: { type: String, default: 'Thêm người nói' },
    visible: { type: Boolean, default: false },
    agentId: { type: String },
    form: {
      type: Object,
      default: () => ({ id: null, audioId: '', sourceName: '', introduce: '' })
    }
  },
  data() {
    return {
      dialogKey: Date.now(),
      saving: false,
      audioSourceTab: 'record',
      // History tab
      playingAudioId: null,
      audioElement: null,
      valueTypeOptions: [],
      // Record tab
      isRecording: false,
      recordingTime: 0,
      recordingTimer: null,
      mediaRecorder: null,
      audioChunks: [],
      recordedBlob: null,
      recordedDuration: 0,
      isPlayingRecorded: false,
      recordedAudioEl: null,
      // Upload tab
      uploadedBlob: null,
      uploadedFileName: '',
      isPlayingUploaded: false,
      uploadedAudioEl: null,
      // Validation
      rules: {
        introduce: [{ required: true, message: 'Vui lòng nhập mô tả', trigger: 'blur' }],
        sourceName: [{ required: true, message: 'Vui lòng nhập tên', trigger: 'blur' }],
        audioId: [{
          validator: (rule, value, callback) => {
            if (this.audioSourceTab === 'history' && !value) {
              callback(new Error('Vui lòng chọn audio'));
            } else if (this.audioSourceTab === 'record' && !this.recordedBlob) {
              callback(new Error('Vui lòng thu âm'));
            } else if (this.audioSourceTab === 'upload' && !this.uploadedBlob) {
              callback(new Error('Vui lòng tải file'));
            } else {
              callback();
            }
          },
          trigger: 'change'
        }]
      }
    };
  },
  methods: {
    // ── Convert any browser audio blob to WAV 16kHz mono ──
    async convertBlobToWav(blob) {
      const arrayBuffer = await blob.arrayBuffer();
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
      audioCtx.close();

      const numSamples = audioBuffer.length;
      const sampleRate = 16000;
      const numChannels = 1;
      const mono = audioBuffer.numberOfChannels > 1
        ? this._mixToMono(audioBuffer)
        : audioBuffer.getChannelData(0);

      const resampled = sampleRate !== audioBuffer.sampleRate
        ? this._resample(mono, audioBuffer.sampleRate, sampleRate)
        : mono;

      const wavBuffer = this._encodeWav(resampled, sampleRate, numChannels);
      return new Blob([wavBuffer], { type: 'audio/wav' });
    },
    _mixToMono(audioBuffer) {
      const ch0 = audioBuffer.getChannelData(0);
      const ch1 = audioBuffer.getChannelData(1);
      const mono = new Float32Array(ch0.length);
      for (let i = 0; i < ch0.length; i++) mono[i] = (ch0[i] + ch1[i]) / 2;
      return mono;
    },
    _resample(samples, fromRate, toRate) {
      const ratio = fromRate / toRate;
      const newLen = Math.round(samples.length / ratio);
      const result = new Float32Array(newLen);
      for (let i = 0; i < newLen; i++) {
        const srcIdx = i * ratio;
        const lo = Math.floor(srcIdx);
        const hi = Math.min(lo + 1, samples.length - 1);
        const frac = srcIdx - lo;
        result[i] = samples[lo] * (1 - frac) + samples[hi] * frac;
      }
      return result;
    },
    _encodeWav(samples, sampleRate, numChannels) {
      const bytesPerSample = 2;
      const dataSize = samples.length * bytesPerSample;
      const buffer = new ArrayBuffer(44 + dataSize);
      const view = new DataView(buffer);
      const writeStr = (offset, str) => { for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i)); };
      writeStr(0, 'RIFF');
      view.setUint32(4, 36 + dataSize, true);
      writeStr(8, 'WAVE');
      writeStr(12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, numChannels, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * numChannels * bytesPerSample, true);
      view.setUint16(32, numChannels * bytesPerSample, true);
      view.setUint16(34, 8 * bytesPerSample, true);
      writeStr(36, 'data');
      view.setUint32(40, dataSize, true);
      let offset = 44;
      for (let i = 0; i < samples.length; i++) {
        const s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        offset += 2;
      }
      return buffer;
    },

    // ── History tab ──
    getAudioIconClass(audioId) {
      return this.playingAudioId === audioId ? 'el-icon-loading' : 'el-icon-video-play';
    },
    playAudio(audioId) {
      if (this.playingAudioId === audioId) {
        if (this.audioElement) { this.audioElement.pause(); this.audioElement = null; }
        this.playingAudioId = null;
        return;
      }
      if (this.audioElement) { this.audioElement.pause(); this.audioElement = null; }
      this.playingAudioId = audioId;
      api.agent.getAudioId(audioId, (res) => {
        if (res.data && res.data.data) {
          this.audioElement = new Audio(getServiceUrl() + `/agent/play/${res.data.data}`);
          this.audioElement.onended = () => { this.playingAudioId = null; this.audioElement = null; };
          this.audioElement.play();
        }
      });
    },

    // ── Record tab ──
    async toggleRecording() {
      if (this.isRecording) {
        this.stopRecording();
      } else {
        await this.startRecording();
      }
    },
    async startRecording() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000, channelCount: 1 } });
        this.audioChunks = [];
        this.recordedBlob = null;
        this.recordingTime = 0;

        this.mediaRecorder = new MediaRecorder(stream, { mimeType: this.getSupportedMimeType() });
        this.mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) this.audioChunks.push(e.data);
        };
        this.mediaRecorder.onstop = () => {
          stream.getTracks().forEach(t => t.stop());
          this.recordedBlob = new Blob(this.audioChunks, { type: this.mediaRecorder.mimeType });
          this.recordedDuration = this.recordingTime;
          this.form.audioId = '__recorded__';
        };

        this.mediaRecorder.start(250);
        this.isRecording = true;
        this.recordingTimer = setInterval(() => { this.recordingTime++; }, 1000);
      } catch (err) {
        this.$message.error('Không thể truy cập microphone. Vui lòng cho phép quyền.');
        console.error('Microphone access error:', err);
      }
    },
    stopRecording() {
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.stop();
      }
      this.isRecording = false;
      if (this.recordingTimer) { clearInterval(this.recordingTimer); this.recordingTimer = null; }
    },
    playRecorded() {
      if (this.isPlayingRecorded && this.recordedAudioEl) {
        this.recordedAudioEl.pause(); this.isPlayingRecorded = false; return;
      }
      if (this.recordedBlob) {
        this.recordedAudioEl = new Audio(URL.createObjectURL(this.recordedBlob));
        this.recordedAudioEl.onended = () => { this.isPlayingRecorded = false; };
        this.recordedAudioEl.play();
        this.isPlayingRecorded = true;
      }
    },
    clearRecording() {
      this.recordedBlob = null;
      this.recordedDuration = 0;
      this.form.audioId = '';
    },
    getSupportedMimeType() {
      const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
      return types.find(t => MediaRecorder.isTypeSupported(t)) || '';
    },

    // ── Upload tab ──
    handleFileChange(file) {
      if (file && file.raw) {
        this.uploadedBlob = file.raw;
        this.uploadedFileName = file.name;
        this.form.audioId = '__uploaded__';
      }
    },
    playUploaded() {
      if (this.isPlayingUploaded && this.uploadedAudioEl) {
        this.uploadedAudioEl.pause(); this.isPlayingUploaded = false; return;
      }
      if (this.uploadedBlob) {
        this.uploadedAudioEl = new Audio(URL.createObjectURL(this.uploadedBlob));
        this.uploadedAudioEl.onended = () => { this.isPlayingUploaded = false; };
        this.uploadedAudioEl.play();
        this.isPlayingUploaded = true;
      }
    },
    clearUpload() {
      this.uploadedBlob = null;
      this.uploadedFileName = '';
      this.form.audioId = '';
    },

    // ── Submit ──
    async submit() {
      this.$refs.form.validate(async (valid) => {
        if (!valid) return;
        this.saving = true;

        try {
          if (this.audioSourceTab === 'record' && this.recordedBlob) {
            await this.registerDirectAudio(this.recordedBlob);
          } else if (this.audioSourceTab === 'upload' && this.uploadedBlob) {
            await this.registerDirectAudio(this.uploadedBlob);
          } else {
            this.$emit('submit', { form: this.form, done: () => { this.saving = false; } });
            setTimeout(() => { this.saving = false; }, 3000);
            return;
          }
        } catch (err) {
          this.$message.error('Đăng ký giọng nói thất bại: ' + (err.message || err));
          this.saving = false;
        }
      });
    },

    async registerDirectAudio(blob) {
      const speakerId = this.form.id || `vp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

      let wavBlob;
      try {
        wavBlob = await this.convertBlobToWav(blob);
      } catch (e) {
        console.warn('WAV conversion failed, sending raw audio:', e);
        wavBlob = blob;
      }

      const formData = new FormData();
      formData.append('speaker_id', speakerId);
      formData.append('file', wavBlob, 'voice.wav');

      const voiceprintUrl = process.env.VUE_APP_VOICEPRINT_URL || window.__VOICEPRINT_URL__ || `${window.location.protocol}//${window.location.hostname}:8100`;
      const apiKey = process.env.VUE_APP_VOICEPRINT_KEY || window.__VOICEPRINT_KEY__ || 'voiceprint-secret-key';

      const res = await fetch(`${voiceprintUrl}/voiceprint/register`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${apiKey}` },
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const result = await res.json();
      if (!result.success) throw new Error(result.message || 'Registration failed');

      this.$emit('submit', {
        form: {
          ...this.form,
          audioId: speakerId,
          _directRegistered: true,
          _speakerId: speakerId,
        },
        done: () => { this.saving = false; }
      });
      this.saving = false;
      this.$message.success(`Đã đăng ký giọng nói "${this.form.sourceName}" thành công!`);
    },

    cancel() {
      this.saving = false;
      this.stopAllAudio();
      if (this.isRecording) this.stopRecording();
      this.dialogKey = Date.now();
      this.$emit('cancel');
    },

    stopAllAudio() {
      if (this.audioElement) { this.audioElement.pause(); this.audioElement = null; }
      if (this.recordedAudioEl) { this.recordedAudioEl.pause(); this.recordedAudioEl = null; }
      if (this.uploadedAudioEl) { this.uploadedAudioEl.pause(); this.uploadedAudioEl = null; }
    },

    formatTime(seconds) {
      const m = Math.floor(seconds / 60);
      const s = seconds % 60;
      return `${m}:${s.toString().padStart(2, '0')}`;
    }
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.audioSourceTab = 'record';
        this.recordedBlob = null;
        this.uploadedBlob = null;
        this.uploadedFileName = '';
        api.agent.getRecentlyFiftyByAgentId(this.agentId, (data) => {
          this.valueTypeOptions = (data.data.data || []).map(item => ({ ...item }));
          if (this.valueTypeOptions.length > 0) {
            this.audioSourceTab = 'history';
          }
        });
      }
    },
    'form.audioId'(newVal) {
      if (!newVal || newVal === '__recorded__' || newVal === '__uploaded__') return;
      if (this.valueTypeOptions.some(item => item.audioId === newVal)) return;
      api.agent.getContentByAudioId(newVal, (data) => {
        this.valueTypeOptions.push({ audioId: newVal, content: data.data.data });
      });
    }
  },
  beforeDestroy() {
    this.stopAllAudio();
    if (this.isRecording) this.stopRecording();
  }
};
</script>

<style>
.custom-param-dialog {
  border-radius: 16px !important;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15) !important;
  border: none !important;
}
.custom-param-dialog .el-dialog__header { display: none; }
.custom-param-dialog .el-dialog__body { padding: 0 !important; border-radius: 16px; }
</style>

<style scoped lang="scss">
.audio-icon { font-size: 20px; cursor: pointer; margin: 0 5px; color: #1890ff; }

.audio-source-tabs {
  .tab-buttons {
    display: flex; gap: 0; margin-bottom: 12px; border-radius: 8px; overflow: hidden;
    border: 1px solid #e2e8f0;
  }
  .tab-btn {
    flex: 1; padding: 8px 12px; border: none; background: #f8fafc; color: #64748b;
    cursor: pointer; font-size: 13px; transition: all 0.2s;
    display: flex; align-items: center; justify-content: center; gap: 4px;
    &:not(:last-child) { border-right: 1px solid #e2e8f0; }
    &.active { background: #3b82f6; color: white; font-weight: 500; }
    &:hover:not(.active) { background: #e2e8f0; }
    i { font-size: 15px; }
  }
  .tab-content { min-height: 60px; }
}

.empty-hint {
  color: #94a3b8; font-size: 13px; text-align: center; padding: 12px 0;
}

.record-area {
  .record-controls {
    display: flex; align-items: center; gap: 12px;
  }
  .record-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 10px 20px; border-radius: 24px; border: 2px solid #3b82f6;
    background: white; color: #3b82f6; cursor: pointer; font-size: 14px; font-weight: 500;
    transition: all 0.3s;
    &:hover { background: #eff6ff; }
    &.recording {
      border-color: #ef4444; color: #ef4444; animation: pulse-border 1.5s infinite;
      &:hover { background: #fef2f2; }
    }
    i { font-size: 18px; }
  }
  .recording-timer { font-size: 20px; font-weight: 600; color: #ef4444; font-variant-numeric: tabular-nums; }
  .recording-indicator {
    display: flex; align-items: center; gap: 8px; margin-top: 10px;
    color: #64748b; font-size: 13px;
  }
  .pulse-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #ef4444;
    animation: pulse-dot 1s infinite;
  }
}

.recorded-preview, .upload-preview { margin-top: 10px; }
.preview-row {
  display: flex; align-items: center; gap: 10px; padding: 8px 12px;
  background: #f0f9ff; border-radius: 8px; border: 1px solid #bfdbfe;
}
.play-btn, .clear-btn {
  width: 32px; height: 32px; border-radius: 50%; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.play-btn { background: #3b82f6; color: white; &:hover { background: #2563eb; } }
.clear-btn { background: #fee2e2; color: #ef4444; &:hover { background: #fecaca; } }
.recorded-info { flex: 1; font-size: 13px; color: #475569; }

.upload-area {
  .upload-box {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    padding: 16px; border: 2px dashed #cbd5e1; border-radius: 8px;
    cursor: pointer; color: #64748b; transition: all 0.2s;
    &:hover { border-color: #3b82f6; color: #3b82f6; background: #f8fafc; }
    i { font-size: 20px; }
  }
}

@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.param-dialog-wrapper {
  .dialog-container { padding: 24px 32px; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }
  .dialog-header { position: relative; margin-bottom: 24px; text-align: center; }
  .dialog-title { font-size: 20px; color: #1e293b; margin: 0; font-weight: 600; }
  .custom-close-btn {
    position: absolute; top: -8px; right: -8px; width: 32px; height: 32px; border-radius: 50%;
    border: none; background: #f1f5f9; color: #64748b; cursor: pointer;
    display: flex; align-items: center; justify-content: center; transition: all 0.3s;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    &:hover { color: #fff; background: #ef4444; transform: rotate(90deg); }
  }
  .param-form {
    .form-item {
      margin-bottom: 20px;
      :deep(.el-form-item__label) { color: #475569; font-weight: 500; font-size: 14px; }
    }
    .custom-input :deep(.el-input__inner),
    .custom-select :deep(.el-input__inner) {
      background: #fff; border-radius: 8px; border: 1px solid #e2e8f0; height: 42px;
      font-size: 14px; color: #334155; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
      &:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.2); }
    }
    .custom-select { width: 100%; }
    .custom-textarea :deep(.el-textarea__inner) {
      background: #fff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 12px 14px;
      font-size: 14px; color: #334155;
      &:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.2); }
    }
  }
  .dialog-footer {
    display: flex; justify-content: center; padding: 16px 0 0; margin-top: 16px;
    .save-btn {
      width: 120px; height: 42px; font-size: 14px; font-weight: 500; border-radius: 8px;
      background: #3b82f6; color: white; border: none;
      &:hover { background: #2563eb; transform: translateY(-1px); }
    }
    .cancel-btn {
      width: 120px; height: 42px; font-size: 14px; border-radius: 8px;
      background: #fff; color: #64748b; border: 1px solid #e2e8f0; margin-left: 16px;
      &:hover { background: #f8fafc; color: #475569; }
    }
  }
}
</style>
