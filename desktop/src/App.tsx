import { useState, type FormEvent } from 'react'
import {
  Bell,
  Bot,
  CalendarDays,
  Circle,
  Cpu,
  Folder,
  HardDrive,
  History,
  ListTodo,
  MemoryStick,
  MessageSquare,
  Mic,
  Paperclip,
  Puzzle,
  Send,
  Settings,
  Sparkles,
  SquareTerminal,
  Wrench,
  Zap,
} from 'lucide-react'
import './App.css'

type Message = {
  id: number
  author: 'user' | 'maymay'
  text: string
  time: string
}

const navigation = [
  { label: 'Conversa', icon: MessageSquare, active: true },
  { label: 'Histórico', icon: History },
  { label: 'Tarefas', icon: ListTodo },
  { label: 'Lembretes', icon: Bell },
  { label: 'Agenda', icon: CalendarDays },
  { label: 'Arquivos', icon: Folder },
  { label: 'Ferramentas', icon: Wrench },
  { label: 'Configurações', icon: Settings },
  { label: 'Plugins', icon: Puzzle },
  { label: 'Terminal', icon: SquareTerminal },
]

const initialMessages: Message[] = [
  {
    id: 1,
    author: 'user',
    text: 'Apresente-se em uma única frase.',
    time: '13:42',
  },
  {
    id: 2,
    author: 'maymay',
    text: 'Olá! Sou MayMay, sua assistente pessoal local dedicada a ajudar com tarefas diárias no seu computador.',
    time: '13:42',
  },
]

function currentTime() {
  return new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date())
}

function App() {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const content = input.trim()

    if (!content) {
      return
    }

    const userMessage: Message = {
      id: Date.now(),
      author: 'user',
      text: content,
      time: currentTime(),
    }

    setMessages((current) => [...current, userMessage])
    setInput('')

    window.setTimeout(() => {
      const assistantMessage: Message = {
        id: Date.now() + 1,
        author: 'maymay',
        text: 'Interface funcionando. A conexão real com o núcleo local será ligada na próxima etapa.',
        time: currentTime(),
      }

      setMessages((current) => [...current, assistantMessage])
    }, 350)
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-symbol">
            <Sparkles size={24} />
          </div>

          <div>
            <strong>MAYMAY</strong>
            <span>ASSISTENTE PESSOAL LOCAL</span>
          </div>
        </div>

        <div className="topbar-signal">
          <span className="signal-line" />
          <span className="online-dot" />
          ONLINE
          <span className="signal-line reverse" />
        </div>

        <div className="window-controls" aria-hidden="true">
          <span>—</span>
          <span>□</span>
          <span>×</span>
        </div>
      </header>

      <aside className="sidebar panel">
        <section>
          <p className="section-title">NAVEGAÇÃO</p>

          <nav className="navigation">
            {navigation.map(({ label, icon: Icon, active }) => (
              <button
                className={active ? 'nav-item active' : 'nav-item'}
                key={label}
                type="button"
              >
                <Icon size={18} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </section>

        <section className="system-section">
          <p className="section-title">STATUS DO SISTEMA</p>

          <div className="status-list">
            <div className="status-row">
              <Bot size={17} />
              <span>Ollama</span>
              <strong className="success">Online</strong>
            </div>

            <div className="status-row">
              <Sparkles size={17} />
              <span>Modelo</span>
              <strong className="success">qwen3.5:4b</strong>
            </div>

            <div className="status-row">
              <Cpu size={17} />
              <span>CPU</span>
              <strong className="success">12%</strong>
            </div>

            <div className="metric-bar">
              <span style={{ width: '28%' }} />
            </div>

            <div className="status-row">
              <MemoryStick size={17} />
              <span>Memória</span>
              <strong className="success">3.2 / 16 GB</strong>
            </div>

            <div className="metric-bar">
              <span style={{ width: '42%' }} />
            </div>

            <div className="status-row">
              <HardDrive size={17} />
              <span>Disco</span>
              <strong className="success">120 GB livres</strong>
            </div>
          </div>
        </section>

        <section className="terminal-card">
          <div className="terminal-header">
            <span>TERMINAL</span>
            <SquareTerminal size={15} />
          </div>

          <div className="terminal-content">
            <p>C:\MayMay&gt; maymay doctor</p>
            <br />
            <p>Ollama: funcionando, versão 0.32.0</p>
            <p>Modelo configurado: qwen3.5:4b</p>
            <p>Modelo: instalado e disponível</p>
            <p>Status: tudo certo!</p>
            <br />
            <p>C:\MayMay&gt; <span className="cursor">_</span></p>
          </div>
        </section>
      </aside>

      <main className="chat-panel panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">CONVERSA ATIVA</span>
            <h1>Olá, Rai.</h1>
          </div>

          <span className="conversation-id">MAY-001</span>
        </div>

        <div className="messages">
          {messages.map((message) => (
            <article
              className={`message ${message.author}`}
              key={message.id}
            >
              {message.author === 'maymay' && (
                <div className="message-avatar">
                  <img
                    src="/maymay-chat-avatar.png"
                    alt="Avatar da MayMay"
                  />
                </div>
              )}

              <div className="message-bubble">
                <p>{message.text}</p>
                <time>{message.time}</time>
              </div>
            </article>
          ))}
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <textarea
            aria-label="Mensagem para a MayMay"
            onChange={(event) => setInput(event.target.value)}
            placeholder="Digite sua mensagem..."
            rows={3}
            value={input}
          />

          <button
            aria-label="Enviar mensagem"
            className="send-button"
            type="submit"
          >
            <Send size={22} />
          </button>
        </form>

        <div className="quick-actions">
          <button type="button">
            <Zap size={17} />
            Ação rápida
          </button>

          <button type="button">
            <Paperclip size={17} />
            Anexar
          </button>

          <button className="highlight" type="button">
            <SquareTerminal size={17} />
            Modo Geek
          </button>

          <button className="voice-button" type="button">
            <Mic size={17} />
            Voz
          </button>
        </div>
      </main>

      <aside className="avatar-panel panel">
        <div className="avatar-heading">
          <div>
            <span className="eyebrow">MAYMAY</span>
            <strong>
              <Circle size={8} fill="currentColor" />
              ONLINE
            </strong>
          </div>
        </div>

        <div className="avatar-stage">
          <div className="avatar-grid" />
          <div className="avatar-ring ring-one" />
          <div className="avatar-ring ring-two" />

          <img
            className="main-avatar"
            src="/maymay-avatar.png"
            alt="MayMay"
          />
        </div>

        <div className="info-grid">
          <div>
            <span>VERSÃO</span>
            <strong>0.1.0</strong>
          </div>

          <div>
            <span>PLATAFORMA</span>
            <strong>Windows</strong>
          </div>

          <div>
            <span>AMBIENTE</span>
            <strong>Local</strong>
          </div>

          <div>
            <span>PYTHON</span>
            <strong>3.12.13</strong>
          </div>
        </div>

        <div className="shortcuts">
          <p className="section-title">ATALHOS GEEK</p>

          <div><code>/ask</code><span>Pergunta rápida</span></div>
          <div><code>/chat</code><span>Iniciar conversa</span></div>
          <div><code>/doctor</code><span>Verificar sistema</span></div>
          <div><code>/help</code><span>Ver ajuda</span></div>
        </div>
      </aside>

      <footer className="footer">
        MAYMAY • ASSISTENTE PESSOAL LOCAL
      </footer>
    </div>
  )
}

export default App
