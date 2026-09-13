import { useEffect } from "react";

export default function PageMeta({ title, description, path = "/", image = "/og-hydrosafe.jpg", structuredData }) {
  useEffect(() => {
    const absoluteUrl = new URL(path, window.location.origin).href;
    const absoluteImage = new URL(image, window.location.origin).href;
    document.title = title;

    const setMeta = (selector, attributes) => {
      let element = document.head.querySelector(selector);
      if (!element) {
        element = document.createElement("meta");
        document.head.appendChild(element);
      }
      Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    };
    setMeta('meta[name="description"]', { name: "description", content: description });
    setMeta('meta[property="og:title"]', { property: "og:title", content: title });
    setMeta('meta[property="og:description"]', { property: "og:description", content: description });
    setMeta('meta[property="og:type"]', { property: "og:type", content: "website" });
    setMeta('meta[property="og:url"]', { property: "og:url", content: absoluteUrl });
    setMeta('meta[property="og:image"]', { property: "og:image", content: absoluteImage });
    setMeta('meta[name="twitter:card"]', { name: "twitter:card", content: "summary_large_image" });
    setMeta('meta[name="twitter:title"]', { name: "twitter:title", content: title });
    setMeta('meta[name="twitter:description"]', { name: "twitter:description", content: description });
    setMeta('meta[name="twitter:image"]', { name: "twitter:image", content: absoluteImage });

    let canonical = document.head.querySelector('link[rel="canonical"]');
    if (!canonical) { canonical = document.createElement("link"); canonical.rel = "canonical"; document.head.appendChild(canonical); }
    canonical.href = absoluteUrl;

    const oldScript = document.getElementById("page-structured-data");
    oldScript?.remove();
    if (structuredData) {
      const script = document.createElement("script");
      script.id = "page-structured-data";
      script.type = "application/ld+json";
      script.textContent = JSON.stringify(structuredData);
      document.head.appendChild(script);
    }
  }, [title, description, path, image, structuredData]);
  return null;
}
