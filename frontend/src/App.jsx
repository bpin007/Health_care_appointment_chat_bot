import { useState } from 'react'
import './App.css'
import ChatScreen from './components/ChatScreen'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div className="h-screen">
        <ChatScreen />
      </div>
    </>
  )
}

export default App
