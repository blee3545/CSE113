#pragma once

#include <atomic>
#include <thread>

class mutex {
 public:
  mutex() {
    thread_count = 0;
    choosing = nullptr;
    ticket = nullptr;
  }

  ~mutex() {
    delete[] choosing;
    delete[] ticket;
  }
  
  void init (int num_threads) {
    // init is called before any thread starts using the lock.
    delete[] choosing;
    delete[] ticket;
    thread_count = num_threads;
    choosing = new std::atomic<bool>[thread_count];
    ticket = new std::atomic<unsigned long long>[thread_count];
    for (int i = 0; i < thread_count; i++) {
      choosing[i].store(false);
      ticket[i].store(0);
    }
  }
  
  void lock(int thread_id) {
    choosing[thread_id].store(true);
    unsigned long long largest_ticket = 0;
    for (int i = 0; i < thread_count; i++) {
      unsigned long long value = ticket[i].load();
      if (value > largest_ticket) {
        largest_ticket = value;
      }
    }
    unsigned long long my_ticket = largest_ticket + 1;
    ticket[thread_id].store(my_ticket);
    choosing[thread_id].store(false);

    for (int i = 0; i < thread_count; i++) {
      if (i == thread_id) {
        continue;
      }
      // Wait for a complete ticket, then compare (ticket, thread id).
      while (choosing[i].load()) {
        std::this_thread::yield();
      }
      while (true) {
        unsigned long long other_ticket = ticket[i].load();
        if (other_ticket == 0 || other_ticket > my_ticket ||
            (other_ticket == my_ticket && i > thread_id)) {
          break;
        }
        std::this_thread::yield();
      }
    }
  }
  
  void unlock(int thread_id) {
    ticket[thread_id].store(0);
  }

 private:
  // Default sequentially consistent loads/stores preserve algorithm order.
  int thread_count;
  std::atomic<bool> *choosing;
  std::atomic<unsigned long long> *ticket;
};
