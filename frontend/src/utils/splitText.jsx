export default function splitText(text) {
  return text.split("").map((char, index) => (
    <span key={index} style={{ "--i": index }}>
      {char === "" ? "\\u00ao" : char}
    </span>
  ));
}
