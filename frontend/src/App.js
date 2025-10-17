import React, { useState } from "react";

function App() {
  const [cnr, setCnr] = useState("");
  const [stateVal, setStateVal] = useState("");
  const [district, setDistrict] = useState("");
  const [courtComplex, setCourtComplex] = useState("");
  const [courtName, setCourtName] = useState("");
  const [date, setDate] = useState("");
  const [caseType, setCaseType] = useState("civ"); // civil/criminal
  const [log, setLog] = useState("");

  // Captcha state
  const [captchaImage, setCaptchaImage] = useState(null);
  const [captchaText, setCaptchaText] = useState("");
  const [sessionId, setSessionId] = useState(null);

  const apiBase = "http://localhost:5000/api";

  const appendLog = (text) => {
    setLog((prev) => `${prev}\n${new Date().toLocaleTimeString()} — ${text}`);
  };

  // ---------------- CNR Workflow ----------------
  const fetchByCnrInit = async () => {
    if (!cnr) {
      appendLog("⚠️ Please enter a valid CNR.");
      return;
    }
    appendLog("⏳ Initializing CNR request...");
    try {
      const res = await fetch(`${apiBase}/fetch_by_cnr_init`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cnr }),
      });
      const j = await res.json();

      if (j.captcha_required) {
        appendLog("🧩 Captcha received — please enter it below.");
        setCaptchaImage(j.captcha_image);
        setSessionId(j.session_id);
      } else if (j.case_info) {
        appendLog(`✅ Case info: ${JSON.stringify(j.case_info)}`);
        if (j.pdf_links?.length) appendLog(`📄 PDF links: ${JSON.stringify(j.pdf_links)}`);
      } else if (j.error) {
        appendLog(`❌ Error: ${j.error}`);
      }
    } catch (e) {
      appendLog(`❌ Error: ${e.message}`);
    }
  };

  const fetchByCnrSubmit = async () => {
    if (!captchaText || !sessionId) {
      appendLog("⚠️ Enter CAPTCHA before submitting.");
      return;
    }
    appendLog("📤 Submitting CAPTCHA for CNR...");
    try {
      const res = await fetch(`${apiBase}/fetch_by_cnr_submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ captcha: captchaText, session_id: sessionId }),
      });
      const j = await res.json();
      if (j.case_info) appendLog(`✅ Case info: ${JSON.stringify(j.case_info)}`);
      if (j.pdfs?.length) appendLog(`📄 PDFs downloaded: ${JSON.stringify(j.pdfs)}`);
      if (j.zip) appendLog(`📦 ZIP available at: ${apiBase}/download_pdf?path=${encodeURIComponent(DOWNLOAD_DIR + "/" + j.zip)}`);
      if (j.error) appendLog(`❌ Error: ${j.error}`);
      setCaptchaImage(null);
      setCaptchaText("");
      setSessionId(null);
    } catch (e) {
      appendLog(`❌ Error: ${e.message}`);
    }
  };

  // ---------------- Court Workflow ----------------
  const fetchByCourtInit = async () => {
    if (!stateVal || !district || !courtComplex || !courtName || !date) {
      appendLog("⚠️ Fill all required fields for Court fetch.");
      return;
    }
    appendLog("⏳ Initializing Court request...");
    try {
      const res = await fetch(`${apiBase}/fetch_by_court_init`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state: stateVal,
          district,
          court_complex_code: courtComplex,
          court_name: courtName,
          date,
        }),
      });
      const j = await res.json();
      if (j.captcha_image) {
        appendLog("🧩 Captcha received — please enter it below.");
        setCaptchaImage(j.captcha_image);
        setSessionId(j.session_id);
      } else if (j.error) {
        appendLog(`❌ Error: ${j.error}`);
      }
    } catch (e) {
      appendLog(`❌ Error: ${e.message}`);
    }
  };

  const fetchByCourtSubmit = async () => {
    if (!captchaText || !sessionId) {
      appendLog("⚠️ Enter CAPTCHA before submitting.");
      return;
    }
    appendLog("📤 Submitting CAPTCHA for Court fetch...");
    try {
      const res = await fetch(`${apiBase}/fetch_by_court_submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ captcha: captchaText, session_id: sessionId, case_type: caseType }),
      });
      const j = await res.json();
      if (j.pdf_path) {
        appendLog(`✅ PDF generated at: ${j.pdf_path}`);
        const link = document.createElement("a");
        link.href = `${apiBase}/download_pdf?path=${encodeURIComponent(j.pdf_path)}`;
        link.download = "cause_list.pdf";
        link.click();
      } else if (j.error) appendLog(`❌ Error: ${j.error}`);
      setCaptchaImage(null);
      setCaptchaText("");
      setSessionId(null);
    } catch (e) {
      appendLog(`❌ Error: ${e.message}`);
    }
  };

  return (
    <div style={{ padding: 20, fontFamily: "Segoe UI, Arial, sans-serif" }}>
      <h2>⚖️ eCourts Fetcher with CAPTCHA</h2>

      {/* CNR Section */}
      <section style={{ marginBottom: 20 }}>
        <h3>Search by CNR</h3>
        <input placeholder="Enter CNR" value={cnr} onChange={(e) => setCnr(e.target.value)} />
        <button onClick={fetchByCnrInit}>Fetch by CNR</button>
        {captchaImage && (
          <div>
            <img src={`data:image/png;base64,${captchaImage}`} alt="Captcha" style={{ marginTop: 10 }} />
            <input placeholder="Enter CAPTCHA" value={captchaText} onChange={(e) => setCaptchaText(e.target.value)} />
            <button onClick={fetchByCnrSubmit}>Submit CAPTCHA</button>
          </div>
        )}
      </section>

      {/* Court Section */}
      <section style={{ marginBottom: 20 }}>
        <h3>Search by Court</h3>
        <input placeholder="State" value={stateVal} onChange={(e) => setStateVal(e.target.value)} />
        <input placeholder="District" value={district} onChange={(e) => setDistrict(e.target.value)} />
        <input placeholder="Court Complex" value={courtComplex} onChange={(e) => setCourtComplex(e.target.value)} />
        <input placeholder="Court Name" value={courtName} onChange={(e) => setCourtName(e.target.value)} />
        <input placeholder="Date (dd-mm-yyyy)" value={date} onChange={(e) => setDate(e.target.value)} />
        <div>
          <label>
            <input type="radio" value="civ" checked={caseType === "civ"} onChange={(e) => setCaseType(e.target.value)} /> Civil
          </label>
          <label>
            <input type="radio" value="cri" checked={caseType === "cri"} onChange={(e) => setCaseType(e.target.value)} /> Criminal
          </label>
        </div>
        <button onClick={fetchByCourtInit}>Fetch by Court</button>
        {captchaImage && (
          <div>
            <img src={`data:image/png;base64,${captchaImage}`} alt="Captcha" style={{ marginTop: 10 }} />
            <input placeholder="Enter CAPTCHA" value={captchaText} onChange={(e) => setCaptchaText(e.target.value)} />
            <button onClick={fetchByCourtSubmit}>Submit CAPTCHA</button>
          </div>
        )}
      </section>

      {/* Logs */}
      <section>
        <h3>Logs</h3>
        <pre style={{ whiteSpace: "pre-wrap", background: "#f4f4f4", padding: 10, minHeight: 200 }}>
          {log || "Logs will appear here..."}
        </pre>
      </section>
    </div>
  );
}

export default App;
