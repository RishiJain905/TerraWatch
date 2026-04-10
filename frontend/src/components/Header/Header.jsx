import './Header.css'

export default function Header({ backendStatus }) {
  return (
    <header className="header">
      <div className="header-left">
        <h1 className="logo">TerraWatch</h1>
        <span className="subtitle">Live GEOINT Platform</span>
      </div>
      <div className="header-right">
        <div className={`status-indicator ${backendStatus}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            {backendStatus === 'checking' ? 'Connecting...' :
             backendStatus === 'ok' ? 'Backend Connected' :
             backendStatus === 'error' ? 'Backend Error' : backendStatus}
          </span>
        </div>
      </div>
    </header>
  )
}
