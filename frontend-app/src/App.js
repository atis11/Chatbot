import React, { useState } from "react";
import axios from "axios";

function App() {
  const [input, setInput] = useState("");
  const [conversation, setConversation] = useState([]);
  const [listening, setListening] = useState(false);
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

  const handleInputChange = (e) => setInput(e.target.value);

  const handleSubmit = async () => {
    if (input.trim() === "") return;
    const userMessage = { sender: "user", text: input };
    setConversation((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const response = await axios.post("http://localhost:5000/ask", { question: input });
      const assistantMessage = { sender: "assistant", text: response.data.answer };
      setConversation((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error:", error);
      const errorMessage = { sender: "assistant", text: "I'm sorry, I couldn't process that request." };
      setConversation((prev) => [...prev, errorMessage]);
    }
  };

  const handleMicClick = () => {
    if (listening) {
      recognition.stop();
      setListening(false);
    } else {
      recognition.start();
      setListening(true);
    }
  };

  recognition.onresult = (event) => {
    const spokenText = event.results[0][0].transcript;
    setInput(spokenText);
    setListening(false);
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    setListening(false);
  };

  // Define micButtonStyle here to access listening state
  const micButtonStyle = {
    padding: "10px",
    borderRadius: "8px",
    backgroundColor: listening ? "#FF0000" : "#4CAF50",
    color: "white",
    border: "none",
    cursor: "pointer",
  };

  const styles = {
    container: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      fontFamily: "Arial, sans-serif",
      padding: "20px",
    },
    chatContainer: {
      display: "flex",
      flexDirection: "column",
      width: "80%",
      maxHeight: "400px",
      overflowY: "auto",
      padding: "10px",
      border: "1px solid #ccc",
      borderRadius: "8px",
      marginBottom: "10px",
    },
    message: {
      padding: "10px",
      borderRadius: "15px",
      margin: "5px",
      maxWidth: "70%",
      wordWrap: "break-word",
    },
    inputContainer: {
      display: "flex",
      alignItems: "center",
      width: "80%",
    },
    input: {
      flex: 1,
      padding: "10px",
      borderRadius: "8px",
      border: "1px solid #ccc",
      marginRight: "5px",
    },
    button: {
      padding: "10px",
      borderRadius: "8px",
      backgroundColor: "#4CAF50",
      color: "white",
      border: "none",
      cursor: "pointer",
      marginRight: "5px",
    },
  };

  return (
    <div style={styles.container}>
      <h2>Voice-Activated Assistant</h2>
      <div style={styles.chatContainer}>
        {conversation.map((msg, index) => (
          <div
            key={index}
            style={{
              ...styles.message,
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              backgroundColor: msg.sender === "user" ? "#e1ffc7" : "#f0f0f0",
            }}
          >
            {msg.text}
          </div>
        ))}
      </div>
      <div style={styles.inputContainer}>
        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          placeholder="Type your question here..."
          style={styles.input}
        />
        <button onClick={handleSubmit} style={styles.button}>Send</button>
        <button onClick={handleMicClick} style={micButtonStyle}>
          {listening ? "🎙️" : "🎤"}
        </button>
      </div>
    </div>
  );
}

export default App;
