import React, { useEffect, useRef, useState } from "react";
import { Button, Field, Input, SpinButton } from "@fluentui/react-components";
import { documentError, useDocumentAction } from "../../Services/documents";

function Drawing({ onPreview }) {
  const canvas = useRef(null);
  const strokes = useRef([]);
  const active = useRef(null);
  const [count, setCount] = useState(0);
  function redraw() {
    const ctx = canvas.current.getContext("2d");
    ctx.clearRect(0, 0, 1000, 360);
    ctx.strokeStyle = "#111a2b"; ctx.fillStyle = "#111a2b";
    ctx.lineWidth = 3; ctx.lineCap = "round"; ctx.lineJoin = "round";
    for (const stroke of strokes.current) {
      ctx.beginPath(); ctx.moveTo(...stroke[0]);
      for (const point of stroke.slice(1)) ctx.lineTo(...point);
      if (stroke.length === 1) { ctx.arc(...stroke[0], 1.5, 0, Math.PI * 2); ctx.fill(); }
      else ctx.stroke();
    }
  }
  // Only the stroke count drives the buttons, so pointer moves never re-render React.
  function changed() { redraw(); setCount(strokes.current.length); }
  function point(event) {
    const rect = canvas.current.getBoundingClientRect();
    return [(event.clientX - rect.left) * 1000 / rect.width, (event.clientY - rect.top) * 360 / rect.height];
  }
  return <div className="dwella-signature-input">
    <p id="draw-instructions">Draw your signature with your finger, pen or mouse. You can also upload a signature.</p>
    <canvas ref={canvas} width={1000} height={360} className="dwella-signature-canvas"
      aria-label="Draw your signature" aria-describedby="draw-instructions"
      onPointerDown={event => {
        if (active.current !== null) return;
        event.currentTarget.setPointerCapture(event.pointerId); active.current = event.pointerId;
        strokes.current.push([point(event)]); changed();
      }} onPointerMove={event => {
        if (active.current !== event.pointerId) return;
        strokes.current.at(-1).push(point(event)); redraw();
      }} onPointerUp={() => { active.current = null; }} onPointerCancel={() => { active.current = null; }} />
    <div className="dwella-document-actions">
      <Button appearance="subtle" disabled={!count} onClick={() => { strokes.current.pop(); changed(); }}>Undo</Button>
      <Button appearance="subtle" disabled={!count} onClick={() => { strokes.current = []; changed(); }}>Clear</Button>
    </div>
    <Button appearance="primary" disabled={!count} onClick={() => canvas.current.toBlob(blob => onPreview(blob, "drawn"), "image/png")}>Preview signature</Button>
  </div>;
}

function Upload({ client, documentId, onPreview }) {
  const image = useRef(null);
  const start = useRef(null);
  const [file, setFile] = useState(null);
  const [page, setPage] = useState(1);
  const [preview, setPreview] = useState(null);
  const [crop, setCrop] = useState({ x: 0, y: 0, width: 100, height: 100 });
  const [error, setError] = useState("");
  const [rotation, setRotation] = useState(0);
  const upload = useDocumentAction(client, documentId, "source-preview", {
    onSuccess: data => { setPreview(data); setCrop({ x: 0, y: 0, width: 100, height: 100 }); setError(""); },
    onError: e => { setPreview(null); setError(documentError(e)); },
  });
  function load(source, number) {
    setError(""); setPreview(null);
    if (!source || source.size > 4 * 1024 ** 2) { setError("Choose a PDF, PNG, JPEG or WebP smaller than 4 MB."); return; }
    const body = new FormData(); body.append("file", source); body.append("page", number);
    upload.mutate(body);
  }
  function coordinates(event) {
    const rect = event.currentTarget.getBoundingClientRect();
    return { x: Math.min(100, Math.max(0, (event.clientX - rect.left) / rect.width * 100)),
      y: Math.min(100, Math.max(0, (event.clientY - rect.top) / rect.height * 100)) };
  }
  function selectSignature() {
    const img = image.current;
    if (!img?.naturalWidth || crop.width < .5 || crop.height < .5) { setError("Select the signature area first."); return; }
    const width = img.naturalWidth * Math.min(crop.width, 100 - crop.x) / 100;
    const height = img.naturalHeight * Math.min(crop.height, 100 - crop.y) / 100;
    const scale = Math.min(1, 1200 / Math.max(width, height));
    const output = document.createElement("canvas");
    const turned = rotation % 180 !== 0;
    output.width = Math.max(1, Math.round((turned ? height : width) * scale));
    output.height = Math.max(1, Math.round((turned ? width : height) * scale));
    const ctx = output.getContext("2d");
    ctx.fillStyle = "white"; ctx.fillRect(0, 0, output.width, output.height);
    ctx.translate(output.width / 2, output.height / 2); ctx.rotate(rotation * Math.PI / 180);
    ctx.drawImage(img, img.naturalWidth * crop.x / 100, img.naturalHeight * crop.y / 100,
      width, height, -width * scale / 2, -height * scale / 2, width * scale, height * scale);
    output.toBlob(blob => onPreview(blob, "uploaded"), "image/png");
  }
  return <div className="dwella-signature-input">
    <Field label="Signature image or PDF" hint="Up to 4 MB. Select only your signature; the original source is not added to the agreement.">
      <Input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" disabled={upload.isPending}
        onChange={event => { const source = event.target.files?.[0]; setFile(source); setPage(1); if (source) load(source, 1); }} />
    </Field>
    {upload.isPending && <p role="status">Preparing a safe preview…</p>}
    {preview && <>
      {preview.pages > 1 && <Field label="Source PDF page"><SpinButton min={1} max={preview.pages} value={page}
        onChange={(_, data) => { const next = Math.min(preview.pages, Math.max(1, Number(data.value ?? data.displayValue) || 1)); setPage(next); load(file, next); }} /></Field>}
      <p>Drag around your signature, or enter the selection percentages below.</p>
      <div className="dwella-crop-stage" onPointerDown={event => {
        start.current = coordinates(event); event.currentTarget.setPointerCapture(event.pointerId);
      }} onPointerMove={event => {
        if (!start.current) return;
        const next = coordinates(event), first = start.current;
        setCrop({ x: Math.min(first.x, next.x), y: Math.min(first.y, next.y), width: Math.abs(next.x - first.x), height: Math.abs(next.y - first.y) });
      }} onPointerUp={() => { start.current = null; }} onPointerCancel={() => { start.current = null; }}>
        <img ref={image} src={`data:image/png;base64,${preview.image}`} alt="Uploaded source. Select the signature region." draggable={false} />
        <span className="dwella-crop-selection" aria-hidden="true" style={{ left: `${crop.x}%`, top: `${crop.y}%`, width: `${crop.width}%`, height: `${crop.height}%` }} />
      </div>
      <div className="dwella-crop-controls">{Object.keys(crop).map(key => <Field key={key} label={`${key[0].toUpperCase() + key.slice(1)} (%)`}>
        <Input type="number" min={key === "width" || key === "height" ? 1 : 0} max={100} value={String(Math.round(crop[key]))}
          onChange={(_, data) => setCrop(current => ({ ...current, [key]: Math.min(100, Math.max(0, Number(data.value) || 0)) }))} />
      </Field>)}</div>
      <div className="dwella-document-actions"><Button onClick={() => setRotation(value => (value + 90) % 360)}>Rotate selection · {rotation}°</Button>
        <Button appearance="primary" onClick={selectSignature}>Preview selected signature</Button></div>
    </>}
    {error && <p role="alert" className="dwella-document-error">{error}</p>}
  </div>;
}

export default function SignatureInput({ client, documentId, onPreview }) {
  const [method, setMethod] = useState("drawn");
  return <>
    <div className="dwella-document-actions" role="group" aria-label="Signature method">
      <Button aria-pressed={method === "drawn"} appearance={method === "drawn" ? "primary" : "secondary"} onClick={() => setMethod("drawn")}>Draw</Button>
      <Button aria-pressed={method === "uploaded"} appearance={method === "uploaded" ? "primary" : "secondary"} onClick={() => setMethod("uploaded")}>Upload image or PDF</Button>
    </div>
    {method === "drawn" ? <Drawing onPreview={onPreview} /> : <Upload client={client} documentId={documentId} onPreview={onPreview} />}
  </>;
}

export function useBlobUrl(blob) {
  const [entry, setEntry] = useState(null);
  useEffect(() => {
    if (!blob) { setEntry(null); return; }
    const value = URL.createObjectURL(blob); setEntry({ blob, url: value });
    return () => URL.revokeObjectURL(value);
  }, [blob]);
  return entry && entry.blob === blob ? entry.url : undefined;
}
