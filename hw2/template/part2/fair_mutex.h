#pragma once

#include <atomic>
#include <mutex>
using namespace std;

class rw_mutex {
 public:
  rw_mutex() {
    writer = false;
    num_readers = 0;
    waiting_writers = 0;
  }

  void lock_reader() {
    bool acquired = false;
    while (!acquired) {
      internal_mutex.lock();
      // New readers cannot pass a writer that is already waiting.
      if (!writer && waiting_writers == 0) {
        num_readers++;
        acquired = true;
      }
      internal_mutex.unlock();
    }
  }
  
  void unlock_reader() {
    internal_mutex.lock();
    num_readers--;
    internal_mutex.unlock();
  }

  
  void lock() {
    internal_mutex.lock();
    waiting_writers++;
    internal_mutex.unlock();

    bool acquired = false;
    while (!acquired) {
      internal_mutex.lock();
      if (!writer && num_readers == 0) {
        waiting_writers--;
        writer = true;
        acquired = true;
      }
      internal_mutex.unlock();
    }
  }
  
  void unlock() {
    internal_mutex.lock();
    writer = false;
    internal_mutex.unlock();
  }

 private:
  // Every access to these counters/flags is protected by internal_mutex.
  mutex internal_mutex;
  bool writer;
  int num_readers;
  int waiting_writers;
};
