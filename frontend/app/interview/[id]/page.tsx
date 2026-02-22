"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic, MicOff, PhoneOff, Loader2, CheckCircle2, AlertCircle,
  Clock, Sparkles, Brain, Shield, Code2, Heart, Briefcase,
  ChevronRight, Volume2, Camera, Eye, FileText, ChevronDown,
} from "lucide-react";
import {
  startInterview,
  submitAnswer,
  getCandidate,
  getEndAndEvaluateStreamUrl,
  type InterviewSession,
  type InterviewQuestion,
  type AnswerResponse,
  type CandidateDetail,
} from "@/lib/api";
import { emotionEngine, type EmotionSnapshot } from "@/lib/emotion-engine";

// ── Agent identity mapping ──────────────────────────────────────────
const AGENT_MAP: Record<string, { label: string; icon: any; color: string; bg: string }> = {
  technical: { label: "Technical Agent", icon: Code2, color: "text-blue-400", bg: "from-blue-500/20 to-blue-600/10" },
  behavioral: { label: "Behavioral Agent", icon: Heart, color: "text-pink-400", bg: "from-pink-500/20 to-pink-600/10" },
  domain: { label: "Domain Agent", icon: Briefcase, color: "text-amber-400", bg: "from-amber-500/20 to-amber-600/10" },
  problem_solving: { label: "Problem Solver", icon: Brain, color: "text-purple-400", bg: "from-purple-500/20 to-purple-600/10" },
  experience_validation: { label: "Experience Agent", icon: Shield, color: "text-emerald-400", bg: "from-emerald-500/20 to-emerald-600/10" },
  general: { label: "AI Interviewer", icon: Sparkles, color: "text-cyan-400", bg: "from-cyan-500/20 to-cyan-600/10" },
};

function agentFor(cat?: string) {
  return AGENT_MAP[cat || "general"] || AGENT_MAP.general;
}

// ── Transcript item type ────────────────────────────────────────────
interface TranscriptItem {
  id: number;
  speaker: "ai" | "user";
  text: string;
  category?: string;
  assessment?: { quality: string; score: number };
}

// ── Sound wave bars for the avatar ──────────────────────────────────
function SoundWave({ active, color }: { active: boolean; color: string }) {
  return (
    <div className="flex items-end gap-[3px] h-8">
      {[0, 1, 2, 3, 4, 3, 2, 1, 0].map((baseH, i) => (
        <motion.div
          key={i}
          className={`w-[3px] rounded-full ${color.replace("text-", "bg-")}`}
          animate={active ? {
            height: [8 + baseH * 3, 16 + Math.random() * 18, 8 + baseH * 3],
          } : { height: 4 }}
          transition={active ? {
            duration: 0.4 + Math.random() * 0.3,
            repeat: Infinity,
            repeatType: "mirror",
            delay: i * 0.05,
          } : { duration: 0.3 }}
        />
      ))}
    </div>
  );
}

// ── Pulsing avatar ring ─────────────────────────────────────────────
function AvatarRing({ speaking, color }: { speaking: boolean; color: string }) {
  const ringColor = color.replace("text-", "ring-");
  return (
    <div className="relative flex items-center justify-center">
      {/* Outer pulse rings */}
      {speaking && (
        <>
          <motion.div
            className={`absolute w-44 h-44 rounded-full border-2 ${color.replace("text-", "border-")} opacity-20`}
            animate={{ scale: [1, 1.3], opacity: [0.3, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
          />
          <motion.div
            className={`absolute w-44 h-44 rounded-full border-2 ${color.replace("text-", "border-")} opacity-20`}
            animate={{ scale: [1, 1.5], opacity: [0.2, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut", delay: 0.5 }}
          />
        </>
      )}
      {/* Main avatar circle */}
      <motion.div
        className={`relative w-36 h-36 rounded-full bg-gradient-to-br ${agentFor().bg} border-2 ${speaking ? color.replace("text-", "border-") : "border-white/10"} flex items-center justify-center shadow-2xl`}
        animate={speaking ? { scale: [1, 1.06, 1] } : { scale: 1 }}
        transition={speaking ? { duration: 1.2, repeat: Infinity, ease: "easeInOut" } : { duration: 0.4 }}
      >
        <Sparkles className={`w-16 h-16 ${color} drop-shadow-lg`} />
      </motion.div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// MAIN PAGE COMPONENT
// ══════════════════════════════════════════════════════════════════════
export default function InterviewPage() {
  const params = useParams();
  const router = useRouter();
  const candidateId = params.id as string;

  // ── State ──────────────────────────────────────────────────────────
  const [phase, setPhase] = useState<"loading" | "ready" | "active" | "processing" | "evaluating" | "complete" | "error">("loading");
  const [candidate, setCandidate] = useState<CandidateDetail | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [currentCategory, setCurrentCategory] = useState("general");
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [timer, setTimer] = useState(900);           // 15 min default
  const [evalProgress, setEvalProgress] = useState<string[]>([]);
  const [questionCount, setQuestionCount] = useState(0);

  // ── In-person transcript & emotion state ───────────────────────
  const [inPersonTranscript, setInPersonTranscript] = useState("");
  const [showTranscriptInput, setShowTranscriptInput] = useState(false);
  const [emotionSnapshot, setEmotionSnapshot] = useState<EmotionSnapshot | null>(null);
  const [faceDetected, setFaceDetected] = useState(false);
  const [emotionReady, setEmotionReady] = useState(false);
  const webcamRef = useRef<HTMLVideoElement>(null);

  // refs — use refs for values accessed inside callbacks to avoid stale closures
  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);
  const finalTranscriptRef = useRef("");
  const liveTranscriptRef = useRef("");
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const nextIdRef = useRef(1);
  const isSubmittingRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const isListeningRef = useRef(false);
  const phaseRef = useRef(phase);
  const sessionIdRef = useRef<string | null>(null);
  const currentQuestionRef = useRef<InterviewQuestion | null>(null);
  const intentionalStopRef = useRef(false);           // distinguish manual stop from browser kill
  const submitVoiceAnswerRef = useRef<(text: string) => void>(() => { });

  // Keep refs synced with state
  useEffect(() => { phaseRef.current = phase; }, [phase]);
  useEffect(() => { sessionIdRef.current = sessionId; }, [sessionId]);

  // ── Load candidate ────────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const c = await getCandidate(candidateId);
        setCandidate(c);
        setPhase("ready");
      } catch (e: any) {
        setError(e.message || "Failed to load candidate");
        setPhase("error");
      }
    })();
  }, [candidateId]);

  // ── Preload voices on mount ───────────────────────────────────────
  useEffect(() => {
    // Chrome loads voices asynchronously — trigger the load early
    window.speechSynthesis.getVoices();
    const handleVoicesChanged = () => window.speechSynthesis.getVoices();
    window.speechSynthesis.addEventListener("voiceschanged", handleVoicesChanged);
    return () => window.speechSynthesis.removeEventListener("voiceschanged", handleVoicesChanged);
  }, []);

  // ── Timer tick ────────────────────────────────────────────────────
  useEffect(() => {
    if (phase !== "active" && phase !== "processing") return;
    const iv = setInterval(() => setTimer((t) => Math.max(0, t - 1)), 1000);
    return () => clearInterval(iv);
  }, [phase]);

  // ── Cleanup emotion engine on unmount ─────────────────────────
  useEffect(() => {
    return () => {
      emotionEngine.destroy();
    };
  }, []);

  // ── Auto-scroll transcript ────────────────────────────────────────
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript, liveTranscript]);

  // ── Format timer ──────────────────────────────────────────────────
  const fmtTime = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  // ════════════════════════════════════════════════════════════════════
  // BEST VOICE PICKER — prioritises Edge Natural > Google > any en
  // ════════════════════════════════════════════════════════════════════
  const pickBestVoice = useCallback((): SpeechSynthesisVoice | null => {
    const voices = window.speechSynthesis.getVoices();
    if (!voices.length) return null;

    const en = voices.filter((v) => v.lang.startsWith("en"));

    // 1) Microsoft Edge "Online (Natural)" voices — extremely human-like
    const edgeNatural = en.find((v) =>
      v.name.includes("Online (Natural)") || v.name.includes("Natural")
    );
    if (edgeNatural) return edgeNatural;

    // 2) Google UK English Female (very natural on Chrome)
    const googleUK = en.find((v) => v.name.includes("Google UK English Female"));
    if (googleUK) return googleUK;

    // 3) Any Google en voice
    const google = en.find((v) => v.name.includes("Google"));
    if (google) return google;

    // 4) macOS Samantha / Karen / Daniel (high quality)
    const mac = en.find((v) =>
      /Samantha|Karen|Daniel|Moira|Tessa/.test(v.name)
    );
    if (mac) return mac;

    // 5) Fallback — first English voice
    return en[0] || null;
  }, []);

  // ════════════════════════════════════════════════════════════════════
  // SPEECH RECOGNITION — all callbacks read from refs, never from state
  // ════════════════════════════════════════════════════════════════════
  const autoRestartRef = useRef(false);   // distinguish fresh start vs browser auto-restart

  const doStartListening = useCallback((isAutoRestart = false) => {
    // Guard: don't start if AI is speaking or we're submitting
    if (isSpeakingRef.current || isSubmittingRef.current) return;
    // Guard: already running
    if (isListeningRef.current) return;
    // Guard: not in active phase
    if (phaseRef.current !== "active") return;

    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setError("Browser doesn't support speech recognition"); return; }

    // Destroy any leftover instance
    try { recognitionRef.current?.abort(); } catch { }

    const recog = new SR();
    recog.continuous = true;
    recog.interimResults = true;
    recog.lang = "en-US";
    recog.maxAlternatives = 3;  // more alternatives = better accuracy

    // Only reset transcript on fresh start (NOT on auto-restart after browser kills it)
    if (!isAutoRestart) {
      finalTranscriptRef.current = "";
      liveTranscriptRef.current = "";
      setLiveTranscript("");
    }
    autoRestartRef.current = isAutoRestart;
    intentionalStopRef.current = false;

    recog.onresult = (e: any) => {
      let interim = "", final_ = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        // Pick the top-confidence alternative
        const best = e.results[i][0];
        const t = best.transcript;
        if (e.results[i].isFinal) final_ += t; else interim += t;
      }
      if (final_) finalTranscriptRef.current += final_;
      const combined = finalTranscriptRef.current + interim;
      liveTranscriptRef.current = combined;
      setLiveTranscript(combined);

      // Reset silence timer — auto-submit after 3.5s of silence (gives more time for pauses)
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = setTimeout(() => {
        const txt = (finalTranscriptRef.current || liveTranscriptRef.current || "").trim();
        if (txt.length > 2 && !isSubmittingRef.current) {
          doStopAndSubmit();
        }
      }, 3500);
    };

    recog.onerror = (e: any) => {
      console.warn("[Mic] error:", e.error);
      // "not-allowed" = user denied permission, "aborted" = we stopped it
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        setError("Microphone access denied. Please allow mic permissions and reload.");
      }
      // For "no-speech" or "network" errors, onend will fire and handle restart
    };

    recog.onend = () => {
      isListeningRef.current = false;
      setIsListening(false);

      // If we didn't intentionally stop, and we're still in active phase,
      // automatically restart recognition (browser killed it after ~60s or no-speech)
      if (
        !intentionalStopRef.current &&
        !isSpeakingRef.current &&
        !isSubmittingRef.current &&
        phaseRef.current === "active"
      ) {
        console.log("[Mic] Recognition ended unexpectedly — restarting (keeping transcript)…");
        setTimeout(() => doStartListening(true), 300);  // true = auto-restart, keep accumulated transcript
      }
    };

    try {
      recog.start();
      recognitionRef.current = recog;
      isListeningRef.current = true;
      setIsListening(true);
      console.log("[Mic] Started listening");
    } catch (err) {
      console.warn("[Mic] Failed to start:", err);
      // Retry once after a short delay
      setTimeout(() => {
        if (!isListeningRef.current && phaseRef.current === "active") {
          try {
            recog.start();
            recognitionRef.current = recog;
            isListeningRef.current = true;
            setIsListening(true);
          } catch { }
        }
      }, 500);
    }
  }, []);   // no state deps — everything is from refs

  const doStopListening = useCallback(() => {
    clearTimeout(silenceTimerRef.current);
    intentionalStopRef.current = true;
    try { recognitionRef.current?.stop(); } catch { }
    isListeningRef.current = false;
    setIsListening(false);
  }, []);

  const doStopAndSubmit = useCallback(() => {
    clearTimeout(silenceTimerRef.current);
    intentionalStopRef.current = true;
    try { recognitionRef.current?.stop(); } catch { }
    isListeningRef.current = false;
    setIsListening(false);

    const txt = (finalTranscriptRef.current || liveTranscriptRef.current || "").trim();
    if (txt.length > 2 && !isSubmittingRef.current) {
      submitVoiceAnswerRef.current(txt);
    }
  }, []);

  // Expose stable references for convenience
  const startListening = doStartListening;
  const stopListening = doStopListening;
  const stopListeningAndSubmit = doStopAndSubmit;

  // ════════════════════════════════════════════════════════════════════
  // TEXT-TO-SPEECH — natural human-like voice
  // ════════════════════════════════════════════════════════════════════
  const speak = useCallback((textOrObj: string | { text: string; suppressAutoListen?: boolean }) => {
    return new Promise<void>((resolve) => {
      // Option: suppress auto-listen after speaking
      let suppressAutoListen = false;
      let text: string;
      if (typeof textOrObj === "object" && textOrObj && textOrObj.text) {
        suppressAutoListen = !!textOrObj.suppressAutoListen;
        text = textOrObj.text;
      } else {
        text = textOrObj as string;
      }
      // Stop any recognition while AI speaks
      doStopListening();
      window.speechSynthesis.cancel();

      const utter = new SpeechSynthesisUtterance(text);

      // Natural speech parameters
      utter.rate = 0.95;       // slightly slower = more natural
      utter.pitch = 1.0;
      utter.volume = 1;

      const voice = pickBestVoice();
      if (voice) {
        utter.voice = voice;
        // Edge Natural voices sound best at rate ~1.0
        if (voice.name.includes("Natural") || voice.name.includes("Online")) {
          utter.rate = 1.0;
        }
      }

      utter.onstart = () => {
        isSpeakingRef.current = true;
        setIsSpeaking(true);
      };

      utter.onend = () => {
        isSpeakingRef.current = false;
        setIsSpeaking(false);
        resolve();
        // Auto-start mic after AI finishes speaking (unless suppressed)
        if (!suppressAutoListen) {
          setTimeout(() => doStartListening(), 400);
        }
      };

      utter.onerror = (ev) => {
        console.warn("[TTS] error:", ev.error);
        isSpeakingRef.current = false;
        setIsSpeaking(false);
        resolve();
        // Still try to start mic even on TTS error (unless suppressed)
        if (!suppressAutoListen) {
          setTimeout(() => doStartListening(), 400);
        }
      };

      window.speechSynthesis.speak(utter);

      // Chrome bug: long utterances get silently paused ~15s in.
      // Workaround: keep poking the synthesis every 5s.
      const keepAlive = setInterval(() => {
        if (window.speechSynthesis.speaking) {
          window.speechSynthesis.pause();
          window.speechSynthesis.resume();
        } else {
          clearInterval(keepAlive);
        }
      }, 5000);

      // Clear the interval when done
      const origOnEnd = utter.onend;
      const origOnError = utter.onerror;
      utter.onend = (ev) => { clearInterval(keepAlive); (origOnEnd as any)?.(ev); };
      utter.onerror = (ev) => { clearInterval(keepAlive); (origOnError as any)?.(ev); };
    });
  }, [pickBestVoice, doStopListening, doStartListening]);

  // ════════════════════════════════════════════════════════════════════
  // START INTERVIEW
  // ════════════════════════════════════════════════════════════════════
  const handleStartInterview = useCallback(async () => {
    if (!candidate) return;
    setPhase("active");
    phaseRef.current = "active";

    // Initialize emotion engine (non-blocking — interview starts even if webcam fails)
    (async () => {
      try {
        const modelsOk = await emotionEngine.loadModels();
        if (modelsOk && webcamRef.current) {
          const camOk = await emotionEngine.startWebcam(webcamRef.current);
          if (camOk) {
            await emotionEngine.startDetection(
              (snap) => setEmotionSnapshot(snap),
              (detected) => setFaceDetected(detected),
            );
            setEmotionReady(true);
            console.log("[Interview] Emotion detection active");
          }
        }
      } catch (err) {
        console.warn("[Interview] Emotion engine failed (non-critical):", err);
      }
    })();

    try {
      const session = await startInterview(
        candidateId, 15,
        inPersonTranscript.trim() || undefined,
      );
      setSessionId(session.session_id);
      sessionIdRef.current = session.session_id;
      setTimer(Math.ceil(session.remaining_seconds || 900));
      setQuestionCount(1);
      currentQuestionRef.current = session.current_question;

      const cat = session.current_question?.category || "general";
      setCurrentCategory(cat);

      // Add AI question to transcript
      const id = nextIdRef.current++;
      setTranscript([{ id, speaker: "ai", text: session.current_question.text, category: cat }]);

      // Speak it — auto-listen will trigger via onend callback
      await speak(session.current_question.text);
    } catch (e: any) {
      setError(e.message || "Failed to start interview");
      setPhase("error");
      phaseRef.current = "error";
    }
  }, [candidate, candidateId, speak, inPersonTranscript]);

  // ════════════════════════════════════════════════════════════════════
  // SUBMIT VOICE ANSWER
  // ════════════════════════════════════════════════════════════════════
  const submitVoiceAnswer = useCallback(async (answerText: string) => {
    if (!sessionIdRef.current || isSubmittingRef.current) return;
    isSubmittingRef.current = true;
    setPhase("processing");
    phaseRef.current = "processing";
    setLiveTranscript("");
    liveTranscriptRef.current = "";

    // Capture emotion snapshot for this answer
    let emotionData: Record<string, any> | undefined;
    if (emotionReady) {
      try {
        const snap = emotionEngine.captureAnswerSnapshot();
        if (snap.frameCount > 0) {
          emotionData = {
            dominant: snap.dominant,
            scores: snap.scores,
            confidence: snap.confidence,
            engagement: snap.engagement,
            stress: snap.stress,
            positivity: snap.positivity,
            frameCount: snap.frameCount,
          };
        }
      } catch (e) { /* emotion capture is non-critical */ }
    }

    // Add user answer to transcript
    const uid = nextIdRef.current++;
    setTranscript((prev) => [...prev, { id: uid, speaker: "user", text: answerText }]);

    try {
      const res: AnswerResponse = await submitAnswer(sessionIdRef.current, answerText, emotionData);

      if (res.remaining_seconds != null) setTimer(Math.ceil(res.remaining_seconds));

      // Time expired → end interview
      if (res.time_expired) {
        isSubmittingRef.current = false;
        await handleEndInterview();
        return;
      }

      // Attach assessment to user message
      if (res.answer_assessment) {
        setTranscript((prev) =>
          prev.map((t) =>
            t.id === uid ? { ...t, assessment: { quality: res.answer_assessment.quality, score: res.answer_assessment.score } } : t
          )
        );
      }

      // ── STEP 1: Speak the agent's REPLY (reaction to the answer) ──
      if (res.reply?.text) {
        const replyCat = res.reply.category || currentCategory;
        setCurrentCategory(replyCat);
        const rid = nextIdRef.current++;
        setTranscript((prev) => [...prev, { id: rid, speaker: "ai", text: res.reply!.text, category: replyCat }]);
        setPhase("active");
        phaseRef.current = "active";
        await speak({ text: res.reply.text, suppressAutoListen: true });
      }

      // ── STEP 2: Speak the NEXT agent's question ──
      if (res.next_question?.text) {
        const cat = res.next_question.category || "general";
        setCurrentCategory(cat);
        setQuestionCount((c) => c + 1);
        currentQuestionRef.current = res.next_question;
        const aid = nextIdRef.current++;
        setTranscript((prev) => [...prev, { id: aid, speaker: "ai", text: res.next_question!.text, category: cat }]);
        setPhase("active");
        phaseRef.current = "active";
        isSubmittingRef.current = false;
        await speak(res.next_question.text);  // speak will auto-start mic via onend
      } else {
        // No more questions
        isSubmittingRef.current = false;
        await handleEndInterview();
      }
    } catch (e: any) {
      console.error("Submit error:", e);
      setPhase("active");
      phaseRef.current = "active";
      isSubmittingRef.current = false;
      // Resume listening on error
      setTimeout(() => doStartListening(), 500);
    }
  }, [speak, doStartListening, emotionReady]);

  // Keep the ref always pointing to the latest submitVoiceAnswer
  useEffect(() => { submitVoiceAnswerRef.current = submitVoiceAnswer; }, [submitVoiceAnswer]);

  // ════════════════════════════════════════════════════════════════════
  // END INTERVIEW → STREAM EVALUATION
  // ════════════════════════════════════════════════════════════════════
  const handleEndInterview = useCallback(async () => {
    const sid = sessionIdRef.current;
    if (!sid) return;
    doStopListening();
    window.speechSynthesis.cancel();

    // Shut down emotion engine
    try {
      emotionEngine.stopDetection();
      emotionEngine.stopWebcam();
    } catch (e) { /* non-critical */ }

    setPhase("evaluating");
    phaseRef.current = "evaluating";
    setEvalProgress([]);

    const url = getEndAndEvaluateStreamUrl(sid);
    const es = new EventSource(url);

    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === "status") {
          setEvalProgress((p) => [...p, data.message]);
        } else if (data.type === "agent_complete") {
          setEvalProgress((p) => [...p, `✓ ${data.agent_name} complete`]);
        } else if (data.type === "complete" || data.type === "final_result") {
          es.close();
          setPhase("complete");
          phaseRef.current = "complete";
          setTimeout(() => router.push(`/evaluation/${candidateId}`), 2000);
        } else if (data.type === "error") {
          es.close();
          setError(data.message || "Evaluation failed");
          setPhase("error");
          phaseRef.current = "error";
        }
      } catch { }
    };
    es.onerror = () => {
      es.close();
      setPhase("complete");
      phaseRef.current = "complete";
      setTimeout(() => router.push(`/evaluation/${candidateId}`), 2500);
    };
  }, [candidateId, router, doStopListening]);

  // ════════════════════════════════════════════════════════════════════
  // MANUAL END INTERVIEW BUTTON
  // ════════════════════════════════════════════════════════════════════
  const handleManualEnd = useCallback(() => {
    doStopListening();
    window.speechSynthesis.cancel();
    handleEndInterview();
  }, [doStopListening, handleEndInterview]);

  // ════════════════════════════════════════════════════════════════════
  // RENDER
  // ════════════════════════════════════════════════════════════════════
  const agent = agentFor(currentCategory);
  const AgentIcon = agent.icon;
  const timerColor = timer <= 60 ? "text-red-400" : timer <= 180 ? "text-amber-400" : "text-white/60";

  // ── Error phase ───────────────────────────────────────────────────
  if (phase === "error") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-red-900/30 border border-red-500/30 rounded-2xl p-8 max-w-md text-center"
        >
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Something went wrong</h2>
          <p className="text-red-300/80 mb-6">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="px-6 py-2.5 bg-white/10 hover:bg-white/20 rounded-xl text-white transition-all"
          >
            Go Home
          </button>
        </motion.div>
      </div>
    );
  }

  // ── Loading phase ─────────────────────────────────────────────────
  if (phase === "loading") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
          >
            <Loader2 className="w-10 h-10 text-cyan-400" />
          </motion.div>
          <p className="text-white/50 text-sm tracking-wide">Preparing interview environment…</p>
        </motion.div>
      </div>
    );
  }

  // ── Ready phase ───────────────────────────────────────────────────
  if (phase === "ready") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="max-w-lg w-full"
        >
          {/* Avatar preview */}
          <div className="flex justify-center mb-8">
            <AvatarRing speaking={false} color="text-cyan-400" />
          </div>

          <h1 className="text-3xl font-bold text-center text-white mb-2">AI Interview</h1>
          <p className="text-center text-white/50 mb-1">
            {candidate?.name || "Candidate"}
          </p>
          <p className="text-center text-white/30 text-sm mb-8">
            15-minute voice interview • Speak naturally and introduce yourself
          </p>

          {/* Tips */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 mb-6 space-y-2">
            <p className="text-white/70 text-sm flex items-start gap-2">
              <Mic className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
              <span>Your mic will <span className="text-cyan-400 font-medium">auto-activate</span> after the AI speaks</span>
            </p>
            <p className="text-white/70 text-sm flex items-start gap-2">
              <Volume2 className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
              <span>Start by introducing yourself — the AI will respond naturally</span>
            </p>
            <p className="text-white/70 text-sm flex items-start gap-2">
              <Clock className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
              <span>Speak clearly; silence for 3 seconds auto-submits your answer</span>
            </p>
            <p className="text-white/70 text-sm flex items-start gap-2">
              <Camera className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
              <span>Your webcam will analyze <span className="text-cyan-400 font-medium">facial expressions</span> during the interview</span>
            </p>
          </div>

          {/* In-person transcript input */}
          <div className="mb-6">
            <button
              onClick={() => setShowTranscriptInput(!showTranscriptInput)}
              className="flex items-center gap-2 text-white/50 hover:text-white/70 text-sm transition-colors w-full justify-center"
            >
              <FileText className="w-4 h-4" />
              <span>Have an in-person interview transcript?</span>
              <ChevronDown className={`w-4 h-4 transition-transform ${showTranscriptInput ? 'rotate-180' : ''}`} />
            </button>
            <AnimatePresence>
              {showTranscriptInput && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden"
                >
                  <div className="mt-3 p-4 bg-white/5 border border-white/10 rounded-xl">
                    <label className="block text-white/60 text-xs font-medium mb-2">
                      Paste the in-person interview transcript below. The AI will analyze it and ask complementary questions.
                    </label>
                    <textarea
                      value={inPersonTranscript}
                      onChange={(e) => setInPersonTranscript(e.target.value)}
                      placeholder="Q: Tell me about your experience...\nA: I have 5 years of experience in...\n\nQ: What's your biggest achievement?\nA: I led a team that..."
                      className="w-full h-32 bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white/80 text-sm placeholder:text-white/20 resize-none focus:outline-none focus:border-cyan-500/40 transition-colors"
                    />
                    {inPersonTranscript.trim() && (
                      <p className="mt-2 text-green-400/70 text-xs flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Transcript loaded ({inPersonTranscript.trim().split('\n').length} lines)
                      </p>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={handleStartInterview}
            className="w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold rounded-xl shadow-lg shadow-cyan-500/25 transition-all"
          >
            Start Interview
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // ── Evaluating phase ──────────────────────────────────────────────
  if (phase === "evaluating") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md w-full text-center"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="mx-auto mb-6"
          >
            <Brain className="w-14 h-14 text-purple-400" />
          </motion.div>
          <h2 className="text-2xl font-bold text-white mb-2">Evaluating Your Interview</h2>
          <p className="text-white/40 text-sm mb-8">8 AI agents are analyzing your performance…</p>

          <div className="space-y-2 text-left">
            <AnimatePresence>
              {evalProgress.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  className="flex items-center gap-3 bg-white/5 rounded-lg px-4 py-2.5"
                >
                  <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
                  <span className="text-white/70 text-sm">{msg}</span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    );
  }

  // ── Complete phase ────────────────────────────────────────────────
  if (phase === "complete") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", stiffness: 200 }}
          className="text-center"
        >
          <motion.div
            animate={{ scale: [1, 1.15, 1] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          >
            <CheckCircle2 className="w-16 h-16 text-green-400 mx-auto mb-4" />
          </motion.div>
          <h2 className="text-2xl font-bold text-white mb-2">Interview Complete!</h2>
          <p className="text-white/40 text-sm">Redirecting to your results…</p>
        </motion.div>
      </div>
    );
  }

  // ══════════════════════════════════════════════════════════════════
  // ACTIVE / PROCESSING PHASE — main split layout
  // ══════════════════════════════════════════════════════════════════
  return (
    <div className="h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex flex-col overflow-hidden">

      {/* ── Top bar ─────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between px-6 py-3 border-b border-white/5 bg-black/30 backdrop-blur-md z-10"
      >
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${phase === "processing" ? "bg-amber-400" : "bg-green-400"} animate-pulse`} />
          <span className="text-white/70 text-sm font-medium">
            {phase === "processing" ? "AI is thinking…" : "Interview Active"}
          </span>
          <span className="text-white/30 text-xs">• Q{questionCount}</span>
        </div>

        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-1.5 ${timerColor} text-sm font-mono`}>
            <Clock className="w-3.5 h-3.5" />
            {fmtTime(timer)}
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleManualEnd}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-xs font-medium transition-all"
          >
            <PhoneOff className="w-3.5 h-3.5" />
            End
          </motion.button>
        </div>
      </motion.div>

      {/* ── Main content: avatar left + transcript right ── */}
      <div className="flex-1 flex overflow-hidden">

        {/* ────────── LEFT: Avatar panel ────────── */}
        <div className="w-1/2 flex flex-col items-center justify-center relative border-r border-white/5">

          {/* Agent label */}
          <motion.div
            key={currentCategory}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute top-6 flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/10"
          >
            <AgentIcon className={`w-4 h-4 ${agent.color}`} />
            <span className={`text-sm font-medium ${agent.color}`}>{agent.label}</span>
          </motion.div>

          {/* Big avatar */}
          <AvatarRing speaking={isSpeaking} color={agent.color} />

          {/* Sound wave visualization */}
          <div className="mt-6">
            <SoundWave active={isSpeaking} color={agent.color} />
          </div>

          {/* Hidden video element for face-api.js (needed even when PIP is hidden) */}
          <video
            ref={webcamRef as React.RefObject<HTMLVideoElement>}
            autoPlay
            muted
            playsInline
            className="hidden"
          />

          {/* Webcam PIP + Emotion overlay */}
          {emotionReady && (
            <div className="absolute bottom-24 left-4 flex flex-col items-start gap-2 z-10">
              {/* mini webcam */}
              <div className="relative rounded-xl overflow-hidden border border-white/10 shadow-lg bg-black/40">
                <video
                  ref={(el) => {
                    if (el && webcamRef.current && webcamRef.current.srcObject) {
                      el.srcObject = webcamRef.current.srcObject;
                    }
                  }}
                  autoPlay
                  muted
                  playsInline
                  className="w-32 h-24 object-cover"
                />
                {/* face detection dot */}
                <div className={`absolute top-1.5 right-1.5 w-2 h-2 rounded-full ${faceDetected ? 'bg-green-400' : 'bg-white/20'} shadow`} />
              </div>

              {/* Emotion badge */}
              {emotionSnapshot && (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-black/60 backdrop-blur-sm border border-white/10 rounded-lg px-3 py-2 w-32"
                >
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Eye className="w-3 h-3 text-purple-400" />
                    <span className="text-[10px] font-semibold text-white/70 capitalize">{emotionSnapshot.dominant}</span>
                    <span className="text-[9px] text-white/30 ml-auto">{Math.round(emotionSnapshot.confidence * 100)}%</span>
                  </div>
                  {/* mini bars */}
                  <div className="space-y-1">
                    <div className="flex items-center gap-1">
                      <span className="text-[8px] text-white/40 w-10">Engage</span>
                      <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full bg-cyan-400 rounded-full transition-all" style={{ width: `${Math.round(emotionSnapshot.engagement * 100)}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-[8px] text-white/40 w-10">Stress</span>
                      <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full bg-amber-400 rounded-full transition-all" style={{ width: `${Math.round(emotionSnapshot.stress * 100)}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-[8px] text-white/40 w-10">Positive</span>
                      <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full bg-green-400 rounded-full transition-all" style={{ width: `${Math.round(emotionSnapshot.positivity * 100)}%` }} />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          )}

          {/* Current question preview */}
          <AnimatePresence mode="wait">
            {transcript.length > 0 && (
              <motion.p
                key={transcript.filter((t) => t.speaker === "ai").length}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.4 }}
                className="mt-8 max-w-sm text-center text-white/60 text-sm leading-relaxed px-4 italic"
              >
                "{transcript.filter((t) => t.speaker === "ai").slice(-1)[0]?.text}"
              </motion.p>
            )}
          </AnimatePresence>

          {/* Mic status indicator */}
          <div className="absolute bottom-8 flex flex-col items-center gap-3">
            {/* Processing spinner */}
            {phase === "processing" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-2 text-amber-400 text-xs"
              >
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating response…
              </motion.div>
            )}

            {/* Mic button */}
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => {
                if (isListening) stopListeningAndSubmit();
                else startListening();
              }}
              disabled={isSpeaking || phase === "processing"}
              className={`w-16 h-16 rounded-full flex items-center justify-center transition-all shadow-xl ${isListening
                ? "bg-red-500 shadow-red-500/30"
                : isSpeaking || phase === "processing"
                  ? "bg-white/10 cursor-not-allowed"
                  : "bg-cyan-500 hover:bg-cyan-400 shadow-cyan-500/30"
                }`}
            >
              {isListening ? (
                <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 0.8, repeat: Infinity }}>
                  <Mic className="w-6 h-6 text-white" />
                </motion.div>
              ) : (
                <MicOff className="w-6 h-6 text-white/70" />
              )}
            </motion.button>

            <span className="text-white/30 text-xs">
              {isListening ? "Listening… (tap to submit)" : isSpeaking ? "AI is speaking…" : phase === "processing" ? "Processing…" : "Tap to speak"}
            </span>
          </div>
        </div>

        {/* ────────── RIGHT: Transcript panel ────────── */}
        <div className="w-1/2 flex flex-col bg-black/20">

          {/* Transcript header */}
          <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
            <span className="text-white/50 text-xs font-medium tracking-wider uppercase">Live Transcript</span>
            <span className="text-white/30 text-xs">{transcript.length} messages</span>
          </div>

          {/* Scrolling transcript */}
          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10">
            <AnimatePresence initial={false}>
              {transcript.map((item) => {
                const isAI = item.speaker === "ai";
                const a = isAI ? agentFor(item.category) : null;
                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35, ease: "easeOut" }}
                    className={`flex ${isAI ? "justify-start" : "justify-end"}`}
                  >
                    <div className={`max-w-[85%] ${isAI ? "" : "text-right"}`}>
                      {/* Speaker label */}
                      <div className={`flex items-center gap-1.5 mb-1 ${isAI ? "" : "justify-end"}`}>
                        {isAI && a && (
                          <>
                            {(() => { const I = a.icon; return <I className={`w-3 h-3 ${a.color}`} />; })()}
                            <span className={`text-[11px] font-medium ${a.color}`}>{a.label}</span>
                          </>
                        )}
                        {!isAI && <span className="text-[11px] font-medium text-white/40">You</span>}
                      </div>

                      {/* Message bubble */}
                      <div
                        className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${isAI
                          ? "bg-white/5 border border-white/10 text-white/80"
                          : "bg-cyan-500/15 border border-cyan-500/20 text-cyan-100/90"
                          }`}
                      >
                        {item.text}
                      </div>

                      {/* Assessment badge */}
                      {item.assessment && (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          className="mt-1 flex items-center gap-1 justify-end"
                        >
                          <span className={`text-[10px] px-2 py-0.5 rounded-full ${item.assessment.score >= 70
                            ? "bg-green-500/20 text-green-400"
                            : item.assessment.score >= 40
                              ? "bg-amber-500/20 text-amber-400"
                              : "bg-red-500/20 text-red-400"
                            }`}>
                            {item.assessment.quality} • {item.assessment.score}
                          </span>
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {/* Live typing indicator */}
            {isListening && liveTranscript && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-end"
              >
                <div className="max-w-[85%] text-right">
                  <span className="text-[11px] font-medium text-white/30">You (live)</span>
                  <div className="rounded-2xl px-4 py-3 text-sm bg-cyan-500/10 border border-cyan-500/15 text-cyan-100/60 italic mt-1">
                    {liveTranscript}
                    <motion.span
                      animate={{ opacity: [1, 0] }}
                      transition={{ duration: 0.6, repeat: Infinity }}
                      className="inline-block ml-0.5 w-0.5 h-4 bg-cyan-400 align-middle"
                    />
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={transcriptEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
