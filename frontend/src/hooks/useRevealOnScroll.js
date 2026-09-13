import { useEffect } from "react";

export function useRevealOnScroll() {
  useEffect(() => {
    const elements = document.querySelectorAll("[data-reveal]");
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.14, rootMargin: "0px 0px -6%" });
    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);
}
