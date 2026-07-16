import { useEffect, useRef, useState, type FormEvent } from 'react'
import {
  Bell,
  CalendarDays,
  Folder,
  History,
  ListTodo,
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

function currentTime() {
  return new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date())
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const messagesRef = useRef<HTMLDivElement>(null)
  const shouldAutoScroll = useRef(true)

  useEffect(() => {
    const container = messagesRef.current

    if (container && shouldAutoScroll.current) {
      container.scrollTop = container.scrollHeight
    }
  }, [messages])

  function handleMessagesScroll() {
    const container = messagesRef.current

    if (!container) {
      return
    }

    const distanceFromBottom =
      container.scrollHeight -
      container.scrollTop -
      container.clientHeight

    shouldAutoScroll.current = distanceFromBottom < 80
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const content = input.trim()

    if (!content || isGenerating) {
      return
    }

    const userMessageId = Date.now()
    const assistantMessageId = userMessageId + 1

    const userMessage: Message = {
      id: userMessageId,
      author: 'user',
      text: content,
      time: currentTime(),
    }

    const conversation = [...messages, userMessage].map(
      (message) => ({
        role:
          message.author === 'user'
            ? 'user'
            : 'assistant',
        content: message.text,
      }),
    )

    const assistantMessage: Message = {
      id: assistantMessageId,
      author: 'maymay',
      text: '',
      time: currentTime(),
    }

    setMessages((current) => [
      ...current,
      userMessage,
      assistantMessage,
    ])

    setInput('')
    setIsGenerating(true)

    try {
      const response = await fetch(
        'http://127.0.0.1:8765/api/chat',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messages: conversation,
          }),
        },
      )

      if (!response.ok) {
        const errorBody = await response.text()

        throw new Error(
          errorBody ||
            `A API respondeu com o status ${response.status}.`,
        )
      }

      if (!response.body) {
        throw new Error(
          'A API não retornou um fluxo de resposta.',
        )
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''

      while (true) {
        const result = await reader.read()

        if (result.done) {
          break
        }

        fullResponse += decoder.decode(
          result.value,
          {
            stream: true,
          },
        )

        setMessages((current) =>
          current.map((message) =>
            message.id === assistantMessageId
              ? {
                  ...message,
                  text: fullResponse,
                }
              : message,
          ),
        )
      }

      fullResponse += decoder.decode()

      if (!fullResponse.trim()) {
        throw new Error(
          'A MayMay não retornou nenhum conteúdo.',
        )
      }

      setMessages((current) =>
        current.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                text: fullResponse,
              }
            : message,
        ),
      )
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : 'Erro desconhecido.'

      setMessages((current) =>
        current.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                text:
                  `Não consegui responder: ${errorMessage}`,
              }
            : message,
        ),
      )
    } finally {
      setIsGenerating(false)
    }
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
      </aside>

      <main className="chat-panel panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">CONVERSA ATIVA</span>
            <h1>Olá, Rai.</h1>
          </div>

          <span className="conversation-id">MAY-001</span>
        </div>

        <div
          className="messages"
          onScroll={handleMessagesScroll}
          ref={messagesRef}
        >
          <div className="messages-list">
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
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <textarea
            aria-label="Mensagem para a MayMay"
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing &&
                !isGenerating &&
                input.trim()
              ) {
                event.preventDefault()
                event.currentTarget.form?.requestSubmit()
              }
            }}
            placeholder="Digite sua mensagem..."
            rows={3}
            value={input}
          />

          <button
            aria-label="Enviar mensagem"
            className="send-button"
            disabled={isGenerating}
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

      <aside
        className="avatar-panel panel"
        aria-label="Avatar da MayMay"
      >
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
      </aside>
    </div>
  )
}

export default App