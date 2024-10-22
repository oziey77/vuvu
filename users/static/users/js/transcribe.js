// Transcribe
var transcribe = {
    // (PART A) PROPERTIES & FLAGS
    hres : null, // html textarea
    htog : null, // html toggle button
    sr : null, // speech recognition object
    listening : false, // speech recognition in progress
  
    // (PART B) INIT
    init : () => {
      // (B1) GET HTML ELEMENTS
      transcribe.hres = document.getElementById("result");
      transcribe.htog = document.getElementById("toggle");
      transcribe.htog.value = "Click to start";
      transcribe.htog.disabled = false;
  
      // (B2) INIT SPEECH RECOGNITION
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      transcribe.sr = new SR();
      transcribe.sr.lang = "en-US";
      transcribe.sr.continuous = true;
      transcribe.sr.interimResults = false;
  
      // (B3) OUTPUT RESULT
      transcribe.sr.onresult = e => {
        let said = e.results[e.results.length-1][0].transcript.trim();
        said = said.charAt(0).toUpperCase() + said.slice(1) + ".";
        document.getElementById("result").value += said + "\n";
      };
  
      // (B4) ON ERROR
      transcribe.sr.onerror = e => {
        console.error(e);
        transcribe.htog.value = "ERROR";
        transcribe.htog.disabled = true;
        alert("Make sure a mic is attached and permission is granted.");
      };
    },
  
    // (PART C) TOGGLE START/STOP RECOGNITION
    toggle : () => {
      if (transcribe.listening) {
        transcribe.sr.stop();
        transcribe.htog.value = "Click to start";
      } else {
        transcribe.sr.start();
        transcribe.htog.value = "Click to stop";
      }
      transcribe.listening = !transcribe.listening;
    }
  };
  
  // (PART D) START
  window.addEventListener("load", transcribe.init);