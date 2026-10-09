const caseSelect = document.querySelector("#case-select");
const caseFields = document.querySelector("#case-fields");
const caseReadonly = document.querySelector("#case-readonly");
const objective = document.querySelector("#objective");
const legalStatus = document.querySelector("#legal-status");
const facts = document.querySelector("#facts");
const contradictions = document.querySelector("#contradictions");
const missingFields = document.querySelector("#missing-fields");
const subjects = document.querySelector("#subjects");
const method = document.querySelector("#method");
const generateButton = document.querySelector("#generate");
const loading = document.querySelector("#loading");
const errorBox = document.querySelector("#error");
const result = document.querySelector("#result");
const meta = document.querySelector("#meta");
const sourceList = document.querySelector("#sources");
const warningList = document.querySelector("#warnings");
const draft = document.querySelector("#draft");
const serviceStatus = document.querySelector("#service-status");
const form = document.querySelector("#draft-form");

let busy = false;
let currentCase = null;

function lines(value) {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

function setError(message) {
  errorBox.hidden = !message;
  errorBox.textContent = message || "";
}

function clearResult() {
  result.hidden = true;
  meta.textContent = "";
  sourceList.replaceChildren();
  warningList.replaceChildren();
  draft.textContent = "";
}

function appendText(parent, tag, text) {
  const node = document.createElement(tag);
  node.textContent = text;
  parent.append(node);
  return node;
}

function fillReadonly(caseData) {
  caseReadonly.replaceChildren();
  const rows = [
    ["Identificador", caseData.case_id],
    ["CUD", caseData.cud],
    ["Departamento", caseData.department],
    ["Fecha de informe", caseData.report_date],
  ];
  rows.forEach(([label, value]) => {
    appendText(caseReadonly, "dt", label);
    appendText(caseReadonly, "dd", value || "");
  });
}

function fillSubjects(people) {
  subjects.replaceChildren();
  (people || []).forEach((person) => {
    const row = document.createElement("div");
    row.className = "subject";
    ["name", "document_type", "document_number", "role"].forEach((key) => {
      const label = document.createElement("label");
      label.textContent = {
        name: "Nombre",
        document_type: "Tipo de documento",
        document_number: "Número de documento",
        role: "Rol",
      }[key];
      const input = document.createElement("input");
      input.dataset.field = key;
      input.value = person[key] || "";
      input.required = true;
      input.maxLength = key === "name" ? 200 : 80;
      label.append(input);
      row.append(label);
    });
    subjects.append(row);
  });
}

function readSubjects() {
  return [...subjects.querySelectorAll(".subject")].map((row) => ({
    name: row.querySelector("[data-field='name']").value.trim(),
    document_type: row.querySelector("[data-field='document_type']").value.trim(),
    document_number: row.querySelector("[data-field='document_number']").value.trim(),
    role: row.querySelector("[data-field='role']").value.trim(),
  }));
}

function showCase(caseData) {
  currentCase = caseData;
  caseFields.hidden = false;
  fillReadonly(caseData);
  objective.value = caseData.objective || "";
  legalStatus.value = caseData.legal_status || "";
  facts.value = (caseData.facts || []).join("\n");
  contradictions.value = (caseData.contradictions || []).join("\n");
  missingFields.value = (caseData.missing_fields || []).join("\n");
  fillSubjects(caseData.subjects || []);
  clearResult();
  setError("");
}

async function readError(response) {
  try {
    const body = await response.json();
    return body.detail || "No se pudo completar la solicitud.";
  } catch (_error) {
    return "No se pudo completar la solicitud.";
  }
}

async function loadCases() {
  const response = await fetch("/api/cases");
  if (!response.ok) {
    setError(await readError(response));
    return;
  }
  const cases = await response.json();
  cases.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.case_id;
    option.textContent = `${item.case_id} — ${item.department}`;
    caseSelect.append(option);
  });
}

async function loadHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) {
      serviceStatus.textContent = "No se pudo consultar el estado del servidor.";
      return;
    }
    const health = await response.json();
    if (health.ollama === "available") {
      serviceStatus.textContent = "El modelo local está disponible. También puede usar la plantilla.";
      return;
    }
    serviceStatus.textContent = "Ollama no está disponible. La plantilla sí puede usarse; la redacción con el modelo fallará hasta que el servicio esté en ejecución.";
  } catch (_error) {
    serviceStatus.textContent = "No se pudo contactar al servidor.";
  }
}

caseSelect.addEventListener("change", async () => {
  clearResult();
  setError("");
  if (!caseSelect.value) {
    caseFields.hidden = true;
    currentCase = null;
    return;
  }
  const response = await fetch(`/api/cases/${encodeURIComponent(caseSelect.value)}`);
  if (!response.ok) {
    setError(await readError(response));
    return;
  }
  showCase(await response.json());
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || !currentCase) {
    return;
  }
  const people = readSubjects();
  if (people.some((person) => !person.name || !person.document_type || !person.document_number || !person.role)) {
    setError("Complete nombre, documento y rol de cada sujeto.");
    return;
  }
  busy = true;
  generateButton.disabled = true;
  loading.textContent = "Generando borrador…";
  setError("");
  clearResult();
  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        case_id: currentCase.case_id,
        method: method.value,
        objective: objective.value.trim(),
        legal_status: legalStatus.value.trim() || null,
        facts: lines(facts.value),
        contradictions: lines(contradictions.value),
        missing_fields: lines(missingFields.value),
        subjects: people,
      }),
    });
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    const body = await response.json();
    result.hidden = false;
    meta.textContent = `Método: ${body.method}. Modelo: ${body.model}. Latencia: ${body.latency_ms} ms.`;
    (body.retrieved_sources || []).forEach((sourceId) => appendText(sourceList, "li", sourceId));
    if (!body.retrieved_sources || body.retrieved_sources.length === 0) {
      appendText(sourceList, "li", "No se recuperaron fuentes.");
    }
    (body.warnings || []).forEach((warning) => appendText(warningList, "li", warning));
    if (!body.warnings || body.warnings.length === 0) {
      appendText(warningList, "li", "No hay advertencias.");
    }
    draft.textContent = body.draft_markdown || "";
  } catch (_error) {
    setError("No se pudo contactar al servidor. Si eligió el modelo, también puede deberse a que Ollama no está disponible o tardó demasiado.");
  } finally {
    busy = false;
    generateButton.disabled = false;
    loading.textContent = "";
  }
});

loadHealth();
loadCases();
