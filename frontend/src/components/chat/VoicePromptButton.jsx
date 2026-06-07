import { useEffect, useRef, useState } from 'react';
import api from '../../api/axios';

const DEFAULT_LANGUAGES = [
  { code: 'en', label: 'EN', title: 'English' },
  { code: 'ne-NP', label: 'ने', title: 'Nepali' },
];

const MIME_CANDIDATES = [
  { mime: 'audio/webm;codecs=opus', extension: 'webm' },
  { mime: 'audio/webm', extension: 'webm' },
  { mime: 'audio/mp4', extension: 'mp4' },
  { mime: 'audio/ogg;codecs=opus', extension: 'ogg' },
];

function supportsRecording() {
  return Boolean(
    typeof window !== 'undefined' &&
    typeof navigator !== 'undefined' &&
    navigator.mediaDevices?.getUserMedia &&
    window.MediaRecorder
  );
}

function pickMimeType() {
  if (typeof window === 'undefined' || !window.MediaRecorder?.isTypeSupported) {
    return { mime: '', extension: 'webm' };
  }
  return MIME_CANDIDATES.find(candidate => window.MediaRecorder.isTypeSupported(candidate.mime)) || {
    mime: '',
    extension: 'webm',
  };
}

export default function VoicePromptButton({
  language,
  onLanguageChange,
  onTranscript,
  disabled = false,
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [notice, setNotice] = useState('');
  const [capabilities, setCapabilities] = useState({
    enabled: true,
    languages: DEFAULT_LANGUAGES,
  });
  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const recordingLanguageRef = useRef(language);
  const mimeRef = useRef({ mime: '', extension: 'webm' });
  const mountedRef = useRef(true);
  const skipTranscriptionRef = useRef(false);

  useEffect(() => {
    let active = true;
    api.get('/voice/capabilities')
      .then(({ data }) => {
        if (!active) return;
        const languages = (data.languages || []).map(item => ({
          code: item.code,
          label: item.code === 'ne-NP' ? 'ने' : 'EN',
          title: item.label,
        }));
        setCapabilities({
          enabled: data.enabled !== false,
          languages: languages.length ? languages : DEFAULT_LANGUAGES,
        });
      })
      .catch(() => {
        if (active) setCapabilities({ enabled: true, languages: DEFAULT_LANGUAGES });
      });
    return () => { active = false; };
  }, []);

  useEffect(() => () => {
    mountedRef.current = false;
    skipTranscriptionRef.current = true;
    recorderRef.current?.state === 'recording' && recorderRef.current.stop();
    streamRef.current?.getTracks().forEach(track => track.stop());
  }, []);

  const transcribeBlob = async (blob, selectedLanguage) => {
    if (!blob.size) {
      if (mountedRef.current) setNotice('No audio captured');
      return;
    }
    setIsTranscribing(true);
    setNotice('Transcribing');
    try {
      const formData = new FormData();
      formData.append('language', selectedLanguage);
      formData.append('file', blob, `prompt-${Date.now()}.${mimeRef.current.extension}`);
      const { data } = await api.post('/voice/transcribe', formData);
      const text = (data.text || '').trim();
      if (text) {
        onTranscript(text);
        if (mountedRef.current) setNotice('');
      } else {
        if (mountedRef.current) setNotice('No speech found');
      }
    } catch (error) {
      if (mountedRef.current) setNotice(error.response?.data?.detail || 'Voice failed');
    } finally {
      if (mountedRef.current) setIsTranscribing(false);
    }
  };

  const stopStream = () => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
  };

  const stopRecording = () => {
    const recorder = recorderRef.current;
    if (recorder?.state === 'recording') {
      recorder.stop();
    }
  };

  const startRecording = async () => {
    if (!supportsRecording()) {
      setNotice('Mic unavailable');
      return;
    }
    if (!capabilities.enabled) {
      setNotice('Voice disabled');
      return;
    }
    setNotice('');
    chunksRef.current = [];
    skipTranscriptionRef.current = false;
    recordingLanguageRef.current = language;
    mimeRef.current = pickMimeType();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const options = mimeRef.current.mime ? { mimeType: mimeRef.current.mime } : undefined;
      const recorder = new window.MediaRecorder(stream, options);
      recorderRef.current = recorder;
      recorder.ondataavailable = event => {
        if (event.data?.size) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeRef.current.mime || 'audio/webm' });
        const shouldTranscribe = !skipTranscriptionRef.current;
        chunksRef.current = [];
        stopStream();
        if (mountedRef.current) setIsRecording(false);
        if (shouldTranscribe) transcribeBlob(blob, recordingLanguageRef.current);
      };
      recorder.start();
      setIsRecording(true);
      setNotice('Listening');
    } catch (_) {
      stopStream();
      setIsRecording(false);
      setNotice('Mic permission needed');
    }
  };

  const busy = disabled || isTranscribing;
  const micDisabled = busy || !capabilities.enabled;

  return (
    <div className="relative flex items-center gap-1">
      <div className="hidden sm:flex items-center rounded border border-slate-200 bg-white overflow-hidden">
        {capabilities.languages.map(item => (
          <button
            key={item.code}
            type="button"
            title={item.title}
            onClick={() => onLanguageChange(item.code)}
            disabled={disabled || isRecording || isTranscribing}
            className={`h-8 min-w-8 px-2 text-[11px] font-semibold transition-colors disabled:opacity-40 ${
              language === item.code
                ? 'bg-slate-900 text-white'
                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
      <button
        type="button"
        title={isRecording ? 'Stop voice input' : 'Start voice input'}
        onClick={isRecording ? stopRecording : startRecording}
        disabled={micDisabled}
        className={`h-9 w-9 inline-flex items-center justify-center rounded transition-all disabled:opacity-40 ${
          isRecording
            ? 'bg-error text-white animate-pulse'
            : 'bg-white text-slate-500 border border-slate-200 hover:text-slate-900 hover:border-slate-300'
        }`}
      >
        <span className="material-symbols-outlined text-[20px]">
          {isTranscribing ? 'hourglass_top' : isRecording ? 'stop_circle' : 'mic'}
        </span>
      </button>
      {notice && (
        <span className="absolute right-0 -top-7 max-w-[140px] truncate rounded bg-slate-900 px-2 py-1 text-[10px] font-medium text-white shadow">
          {notice}
        </span>
      )}
    </div>
  );
}
