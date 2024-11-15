async function sendText() {
    const textInput = document.getElementById('text-input').value;
    if (!textInput) return;

    displayMessage(textInput, 'user');
    document.getElementById('text-input').value = '';

    const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textInput })
    });

    const data = await response.json();
    displayMessage(data.response, 'bot');
}

let isRecording = false;
let mediaRecorder;
let audioChunks = [];

function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            isRecording = true;
            document.getElementById('mic-button').innerText = "🔴";
            document.getElementById('recording-status').innerText = "Recording...";

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                audioChunks = [];
                console.log(audioBlob);
                sendAudioFile(audioBlob);
                isRecording = false;
                document.getElementById('mic-button').innerText = "🎤";
                document.getElementById('recording-status').innerText = "";
            };
        })
        .catch(error => {
            console.error("Error accessing microphone:", error);
        });
}

function stopRecording() {
    mediaRecorder.stop();
}

async function sendAudioFile(audioBlob) {
    const formData = new FormData();
    
    // Append the blob with a filename
    formData.append("audio", audioBlob, "audio.wav");
    console.log(audioBlob.type);

    // Log FormData contents to verify that it's populated
    console.log("FormData contents:");
    for (let pair of formData.entries()) {
        console.log(`${pair[0]}: ${pair[1]}`);
    }

    try {
        // Send the audio file to the server
        const response = await fetch("/audio", { method: "POST", body: formData });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        displayMessage(data.response, 'bot');

    } catch (error) {
        console.error("Error uploading audio:", error);
    }
}


function displayMessage(text, sender) {
    const chatDisplay = document.getElementById('chat-display');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
    messageDiv.innerText = text;
    chatDisplay.appendChild(messageDiv);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

