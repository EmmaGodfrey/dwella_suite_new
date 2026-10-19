import React, { useState } from "react";
import { Image24Regular } from "@fluentui/react-icons";
import { resolveMediaUrl } from "../../Services/apiClient";

export function PropertyPhoto({ src, name = "Property", className = "" }) {
  const [failedSource, setFailedSource] = useState(null);
  return (
    <div className={`dwella-property-photo ${className}`}>
      {src && failedSource !== src ? (
        <img
          src={src.startsWith("blob:") ? src : resolveMediaUrl(src)}
          alt={name}
          loading="lazy"
          onError={() => setFailedSource(src)}
        />
      ) : (
        <span className="dwella-photo-placeholder">
          <Image24Regular />
          <span>No photo</span>
        </span>
      )}
    </div>
  );
}
