// message logger utility for terminal-style message management

export type MessageType = 'system' | 'input' | 'output' | 'success' | 'error';

export interface Message {
  type: MessageType;
  text: string;
  timestamp?: number;
}

/**
 * creates a message logger that manages a message history
 */
export function createMessageLogger() {
  let messages = $state<Message[]>([]);

  return {
    get messages() {
      return messages;
    },
    
    add(type: MessageType, text: string) {
      messages = [...messages, { type, text, timestamp: Date.now() }];
    },

    addSystem(text: string) {
      this.add('system', text);
    },

    addInput(text: string) {
      this.add('input', `> ${text}`);
    },

    addOutput(text: string) {
      this.add('output', text);
    },

    addSuccess(text: string) {
      this.add('success', `[ok] ${text}`);
    },

    addError(text: string) {
      this.add('error', `[err] ${text}`);
    },

    clear() {
      messages = [];
    },

    addMultiple(type: MessageType, texts: string[]) {
      const newMessages = texts.map(text => ({ 
        type, 
        text, 
        timestamp: Date.now() 
      }));
      messages = [...messages, ...newMessages];
    }
  };
}

export type MessageLogger = ReturnType<typeof createMessageLogger>;
