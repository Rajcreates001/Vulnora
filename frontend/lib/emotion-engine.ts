/**
 * Emotion Detection Engine — Real-time facial expression analysis using face-api.js
 *
 * Provides:
 *  - Webcam management
 *  - Continuous face detection + expression recognition (every 500ms)
 *  - Per-answer emotion snapshots
 *  - Session-level emotion timeline
 *  - Temporal smoothing for high-accuracy results
 *  - Confidence-weighted scoring
 *  - Neutral baseline calibration
 */

import * as faceapi from "face-api.js";

// ── Emotion Types ─────────────────────────────────────────────────
export interface EmotionFrame {
  timestamp: number;
  emotions: EmotionScores;
  confidence: number;
  faceDetected: boolean;
}

export interface EmotionScores {
  neutral: number;
  happy: number;
  sad: number;
  angry: number;
  fearful: number;
  disgusted: number;
  surprised: number;
}

export interface EmotionSnapshot {
  dominant: string;
  scores: EmotionScores;
  confidence: number;
  frameCount: number;
  engagement: number;        // 0-100, derived from non-neutral emotions
  stress: number;            // 0-100, derived from negative emotions
  positivity: number;        // 0-100, derived from positive emotions
}

export interface EmotionTimeline {
  frames: EmotionFrame[];
  snapshots: EmotionSnapshot[];     // per-answer snapshots
  sessionAverage: EmotionSnapshot;
  calibrationBaseline: EmotionScores | null;
}

// ── Constants ─────────────────────────────────────────────────────
const DETECTION_INTERVAL_MS = 500;
const SMOOTHING_WINDOW = 5;       // Average over last 5 frames
const MIN_CONFIDENCE = 0.5;       // Minimum face detection confidence
const CALIBRATION_FRAMES = 10;    // Frames used to establish neutral baseline

const EMPTY_SCORES: EmotionScores = {
  neutral: 0, happy: 0, sad: 0, angry: 0,
  fearful: 0, disgusted: 0, surprised: 0,
};

// ── Engine Class ──────────────────────────────────────────────────
class EmotionEngine {
  private videoElement: HTMLVideoElement | null = null;
  private stream: MediaStream | null = null;
  private detectionInterval: ReturnType<typeof setInterval> | null = null;
  private modelsLoaded = false;
  private isRunning = false;

  // Data store
  private frames: EmotionFrame[] = [];
  private currentAnswerFrames: EmotionFrame[] = [];
  private snapshots: EmotionSnapshot[] = [];
  private calibrationBaseline: EmotionScores | null = null;
  private calibrationFrames: EmotionFrame[] = [];
  private isCalibrating = false;

  // Callbacks
  private onEmotionUpdate: ((snapshot: EmotionSnapshot) => void) | null = null;
  private onFaceDetectionChange: ((detected: boolean) => void) | null = null;

  // ── Model Loading ───────────────────────────────────────────────
  async loadModels(): Promise<boolean> {
    if (this.modelsLoaded) return true;
    try {
      const MODEL_URL = "/models";
      await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
        faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
        faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
      ]);
      this.modelsLoaded = true;
      console.log("[EmotionEngine] Models loaded successfully");
      return true;
    } catch (err) {
      console.error("[EmotionEngine] Failed to load models:", err);
      return false;
    }
  }

  // ── Webcam Management ───────────────────────────────────────────
  async startWebcam(videoEl: HTMLVideoElement): Promise<boolean> {
    try {
      this.videoElement = videoEl;
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 320 },
          height: { ideal: 240 },
          facingMode: "user",
          frameRate: { ideal: 15 },
        },
      });
      videoEl.srcObject = this.stream;
      await new Promise<void>((resolve) => {
        videoEl.onloadedmetadata = () => {
          videoEl.play();
          resolve();
        };
      });
      console.log("[EmotionEngine] Webcam started");
      return true;
    } catch (err) {
      console.error("[EmotionEngine] Webcam access failed:", err);
      return false;
    }
  }

  stopWebcam(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
    if (this.videoElement) {
      this.videoElement.srcObject = null;
      this.videoElement = null;
    }
  }

  // ── Detection Loop ──────────────────────────────────────────────
  async startDetection(
    onEmotionUpdate?: (snapshot: EmotionSnapshot) => void,
    onFaceChange?: (detected: boolean) => void,
  ): Promise<void> {
    if (!this.modelsLoaded || !this.videoElement) {
      console.warn("[EmotionEngine] Models or video not ready");
      return;
    }
    if (this.isRunning) return;

    this.onEmotionUpdate = onEmotionUpdate || null;
    this.onFaceDetectionChange = onFaceChange || null;
    this.isRunning = true;

    // Start calibration
    this.isCalibrating = true;
    this.calibrationFrames = [];

    this.detectionInterval = setInterval(() => this.detectFrame(), DETECTION_INTERVAL_MS);
    console.log("[EmotionEngine] Detection started");
  }

  stopDetection(): void {
    if (this.detectionInterval) {
      clearInterval(this.detectionInterval);
      this.detectionInterval = null;
    }
    this.isRunning = false;
    console.log("[EmotionEngine] Detection stopped");
  }

  // ── Per-frame detection ─────────────────────────────────────────
  private async detectFrame(): Promise<void> {
    if (!this.videoElement || this.videoElement.paused || this.videoElement.ended) return;

    try {
      const detection = await faceapi
        .detectSingleFace(this.videoElement, new faceapi.TinyFaceDetectorOptions({
          inputSize: 224,
          scoreThreshold: 0.4,
        }))
        .withFaceLandmarks()
        .withFaceExpressions();

      const now = Date.now();

      if (detection) {
        const expr = detection.expressions;
        const confidence = detection.detection.score;

        const frame: EmotionFrame = {
          timestamp: now,
          emotions: {
            neutral: expr.neutral,
            happy: expr.happy,
            sad: expr.sad,
            angry: expr.angry,
            fearful: expr.fearful,
            disgusted: expr.disgusted,
            surprised: expr.surprised,
          },
          confidence,
          faceDetected: true,
        };

        if (confidence >= MIN_CONFIDENCE) {
          this.frames.push(frame);
          this.currentAnswerFrames.push(frame);

          // Calibration phase
          if (this.isCalibrating) {
            this.calibrationFrames.push(frame);
            if (this.calibrationFrames.length >= CALIBRATION_FRAMES) {
              this.calibrationBaseline = this.averageScores(this.calibrationFrames.map((f) => f.emotions));
              this.isCalibrating = false;
              console.log("[EmotionEngine] Calibration complete:", this.calibrationBaseline);
            }
          }

          // Compute smoothed snapshot and notify
          const snapshot = this.computeSmoothedSnapshot(this.currentAnswerFrames);
          this.onEmotionUpdate?.(snapshot);
        }

        this.onFaceDetectionChange?.(true);
      } else {
        // No face detected
        const frame: EmotionFrame = {
          timestamp: now,
          emotions: { ...EMPTY_SCORES },
          confidence: 0,
          faceDetected: false,
        };
        this.frames.push(frame);
        this.currentAnswerFrames.push(frame);
        this.onFaceDetectionChange?.(false);
      }
    } catch (err) {
      // Silently handle detection errors (can happen with rapid tab switches)
    }
  }

  // ── Smoothing & Aggregation ─────────────────────────────────────
  private computeSmoothedSnapshot(frames: EmotionFrame[]): EmotionSnapshot {
    const validFrames = frames.filter((f) => f.faceDetected && f.confidence >= MIN_CONFIDENCE);
    if (validFrames.length === 0) {
      return {
        dominant: "unknown",
        scores: { ...EMPTY_SCORES },
        confidence: 0,
        frameCount: 0,
        engagement: 0,
        stress: 0,
        positivity: 0,
      };
    }

    // Use last N frames for smoothing (temporal window)
    const window = validFrames.slice(-SMOOTHING_WINDOW);
    const avgScores = this.averageScores(window.map((f) => f.emotions));
    const avgConfidence = window.reduce((s, f) => s + f.confidence, 0) / window.length;

    // Apply baseline calibration (subtract neutral baseline shift)
    let calibrated = avgScores;
    if (this.calibrationBaseline) {
      calibrated = this.applyCalibration(avgScores, this.calibrationBaseline);
    }

    // Determine dominant emotion
    const dominant = this.getDominant(calibrated);

    // Compute composite metrics
    const engagement = Math.min(100, Math.round(
      (1 - calibrated.neutral) * 100
    ));
    const stress = Math.min(100, Math.round(
      (calibrated.angry + calibrated.fearful + calibrated.sad + calibrated.disgusted) * 100
    ));
    const positivity = Math.min(100, Math.round(
      (calibrated.happy + calibrated.surprised * 0.5) * 100
    ));

    return {
      dominant,
      scores: calibrated,
      confidence: avgConfidence,
      frameCount: validFrames.length,
      engagement,
      stress,
      positivity,
    };
  }

  private averageScores(scoresList: EmotionScores[]): EmotionScores {
    if (scoresList.length === 0) return { ...EMPTY_SCORES };
    const n = scoresList.length;
    const sum: EmotionScores = { ...EMPTY_SCORES };
    for (const s of scoresList) {
      sum.neutral += s.neutral;
      sum.happy += s.happy;
      sum.sad += s.sad;
      sum.angry += s.angry;
      sum.fearful += s.fearful;
      sum.disgusted += s.disgusted;
      sum.surprised += s.surprised;
    }
    return {
      neutral: sum.neutral / n,
      happy: sum.happy / n,
      sad: sum.sad / n,
      angry: sum.angry / n,
      fearful: sum.fearful / n,
      disgusted: sum.disgusted / n,
      surprised: sum.surprised / n,
    };
  }

  private applyCalibration(scores: EmotionScores, baseline: EmotionScores): EmotionScores {
    // Shift scores relative to baseline, then re-normalize
    const shifted: EmotionScores = {
      neutral: Math.max(0, scores.neutral - baseline.neutral * 0.3),
      happy: Math.max(0, scores.happy + baseline.neutral * 0.05),
      sad: Math.max(0, scores.sad),
      angry: Math.max(0, scores.angry),
      fearful: Math.max(0, scores.fearful),
      disgusted: Math.max(0, scores.disgusted),
      surprised: Math.max(0, scores.surprised),
    };
    // Re-normalize to sum to 1
    const total = Object.values(shifted).reduce((a, b) => a + b, 0);
    if (total > 0) {
      return {
        neutral: shifted.neutral / total,
        happy: shifted.happy / total,
        sad: shifted.sad / total,
        angry: shifted.angry / total,
        fearful: shifted.fearful / total,
        disgusted: shifted.disgusted / total,
        surprised: shifted.surprised / total,
      };
    }
    return shifted;
  }

  private getDominant(scores: EmotionScores): string {
    let max = -1;
    let label = "neutral";
    for (const [key, val] of Object.entries(scores)) {
      if (val > max) { max = val; label = key; }
    }
    return label;
  }

  // ── Answer boundary management ──────────────────────────────────
  /**
   * Called when the candidate finishes answering.
   * Captures a snapshot of emotions during this answer and resets the buffer.
   */
  captureAnswerSnapshot(): EmotionSnapshot {
    const snapshot = this.computeSmoothedSnapshot(this.currentAnswerFrames);
    this.snapshots.push(snapshot);
    this.currentAnswerFrames = [];   // reset for next answer
    return snapshot;
  }

  // ── Full session data ───────────────────────────────────────────
  getTimeline(): EmotionTimeline {
    return {
      frames: this.frames,
      snapshots: this.snapshots,
      sessionAverage: this.computeSmoothedSnapshot(this.frames),
      calibrationBaseline: this.calibrationBaseline,
    };
  }

  getSessionSummary(): EmotionSnapshot {
    return this.computeSmoothedSnapshot(this.frames);
  }

  getCurrentSnapshot(): EmotionSnapshot {
    return this.computeSmoothedSnapshot(this.currentAnswerFrames);
  }

  isActive(): boolean {
    return this.isRunning;
  }

  getFrameCount(): number {
    return this.frames.length;
  }

  // ── Cleanup ─────────────────────────────────────────────────────
  destroy(): void {
    this.stopDetection();
    this.stopWebcam();
    this.frames = [];
    this.currentAnswerFrames = [];
    this.snapshots = [];
    this.calibrationBaseline = null;
    this.calibrationFrames = [];
  }
}

// Singleton export
export const emotionEngine = new EmotionEngine();
export default emotionEngine;
