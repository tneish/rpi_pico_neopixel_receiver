class RingBuffer:
    def __init__(self, size):
        self.size = size
        self.buffer = [None] * size
        self.head = 0
        self.tail = 0
        self.full = False

    def is_empty(self):
        return ((not self.full) and (self.head == self.tail))

    def is_full(self):
        return self.full

    def enqueue(self, data):
        self.buffer[self.head] = data
        self.head = (self.head + 1) % self.size

        if self.full:
            self.tail = (self.tail + 1) % self.size

        self.full = (self.head == self.tail)

    def dequeue(self):
        if self.is_empty():
            print("Buffer empty!")
            assert(0)

        data = self.buffer[self.tail]
    
        self.tail = (self.tail + 1) % self.size
        self.full = False
        
        return data

    def num_frames(self):
        if (self.head > self.tail):
            return self.head - self.tail
        else:
            return self.size - (self.tail - self.head)

    def peek(self):
        if self.is_empty():
            return None
        
        data = self.buffer[self.tail]
        return data

