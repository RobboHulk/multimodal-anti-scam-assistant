// Microphone.jsx
import React, { useState, useRef } from "react";
import styles from "./Microphone.module.css";

const Microphone = ({ onAudioCapture, disabled = false }) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  const startRecording = async () => {
    if (disabled) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });
        const audioUrl = URL.createObjectURL(audioBlob);

        if (onAudioCapture) {
          onAudioCapture(audioBlob, audioUrl);
        }

        audioChunksRef.current = [];
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("无法访问麦克风:", error);
      alert("请允许访问麦克风权限");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <button
      className={`${styles.micButton} ${isRecording ? styles.recording : styles.norecord}`}
      onClick={isRecording ? stopRecording : startRecording}
      disabled={disabled}
    >
      {!isRecording && (
        <svg viewBox="0 0 1024 1024" width="22" height="22">
          <path
            d="M544 851.946667V906.666667a32 32 0 0 1-64 0v-54.72C294.688 835.733333 149.333333 680.170667 149.333333 490.666667v-21.333334a32 32 0 0 1 64 0v21.333334c0 164.949333 133.717333 298.666667 298.666667 298.666666s298.666667-133.717333 298.666667-298.666666v-21.333334a32 32 0 0 1 64 0v21.333334c0 189.514667-145.354667 345.066667-330.666667 361.28zM298.666667 298.56C298.666667 180.8 394.165333 85.333333 512 85.333333c117.781333 0 213.333333 95.541333 213.333333 213.226667v192.213333C725.333333 608.533333 629.834667 704 512 704c-117.781333 0-213.333333-95.541333-213.333333-213.226667V298.56z m64 0v192.213333C362.666667 573.12 429.557333 640 512 640c82.496 0 149.333333-66.805333 149.333333-149.226667V298.56C661.333333 216.213333 594.442667 149.333333 512 149.333333c-82.496 0-149.333333 66.805333-149.333333 149.226667z"
            fill="currentColor"
          />
        </svg>
      )}
      {isRecording && (
        <ul className={styles.lines}>
          <li className={styles.line}></li>
          <li className={styles.line}></li>
          <li className={styles.line}></li>
          <li className={styles.line}></li>
          <li className={styles.line}></li>
        </ul>
      )}
    </button>
  );
};

export default Microphone;
