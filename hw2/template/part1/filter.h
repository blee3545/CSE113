#pragma once

#include <atomic>
#include <thread>

class mutex {
 public:
  mutex() {
    thread_count = 0;
    level = nullptr;
    victim = nullptr;
  }

  ~mutex() {
    delete[] level;
    delete[] victim;
  }
  
  void init (int num_threads) {
    // init is called before any thread starts using the lock.
    delete[] level;
    delete[] victim;
    thread_count = num_threads;
    level = new std::atomic<int>[thread_count];
    victim = new std::atomic<int>[thread_count];
    for (int i = 0; i < thread_count; i++) {
      level[i].store(0);
      victim[i].store(-1);
    }
  }
  
  void lock(int thread_id) {
    // Pass through N-1 levels. The last arrival at a level waits
    // while another thread is at that level or a higher one.
    for (int current_level = 1; current_level < thread_count; current_level++) {
      level[thread_id].store(current_level);
      victim[current_level].store(thread_id);
      while (true) {
        bool other_thread = false;
        for (int i = 0; i < thread_count; i++) {
          if (i != thread_id && level[i].load() >= current_level) {
            other_thread = true;
            break;
          }
        }
        if (!other_thread || victim[current_level].load() != thread_id) {
          break;
        }
        std::this_thread::yield();
      }
    }
  }
  
  void unlock(int thread_id) {
    level[thread_id].store(0);
  }

 private:
  // Default sequentially consistent loads/stores preserve algorithm order.
  int thread_count;
  std::atomic<int> *level;
  std::atomic<int> *victim;
};
