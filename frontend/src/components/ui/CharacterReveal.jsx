export default function CharacterReveal({ text, as: Tag = "span", className = "" }) {
  let characterIndex = 0;
  return (
    <Tag className={`character-reveal ${className}`} aria-label={text}>
      {text.split(" ").map((word, wordIndex, words) => (
        <span className="character-word" aria-hidden="true" key={`${word}-${wordIndex}`}>
          {Array.from(word).map((character) => {
            const index = characterIndex++;
            return <span className="character-letter" key={`${character}-${index}`} style={{ "--char-index": index }}>{character}</span>;
          })}
          {wordIndex < words.length - 1 && <span className="character-space">&nbsp;</span>}
        </span>
      ))}
    </Tag>
  );
}
