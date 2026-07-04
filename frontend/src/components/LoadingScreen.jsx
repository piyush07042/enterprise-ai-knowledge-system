import "./LoadingScreen.css";

export default function LoadingScreen() {
  return (
    <div className="loading-container">
      <div className="logo-circle">🧠</div>
      <h1>Enterprise AI</h1>
      <div className="spinner"></div>
      <p>Loading...</p>
    </div>
  );
}