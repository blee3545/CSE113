#include <atomic>
#include <cassert>
#include <iostream>
#include <thread>
#include <vector>
#include "fair_mutex.h"

int main() {
  rw_mutex m;
  std::atomic<int> arrived(0);
  // Both readers must acquire before either releases: detects accidental
  // serialization of readers. The runner supplies a timeout for deadlocks.
  auto simultaneous_reader = [&]() {
    m.lock_reader();
    arrived.fetch_add(1);
    while (arrived.load() < 2) std::this_thread::yield();
    m.unlock_reader();
  };
  std::thread first(simultaneous_reader), second(simultaneous_reader);
  first.join();
  second.join();

  int value = 0;
  std::atomic<int> readers(0), writers(0);
  std::vector<std::thread> workers;
  for (int id = 0; id < 8; id++) {
    workers.emplace_back([&, id]() {
      for (int i = 0; i < 3000; i++) {
        if (id < 6) {
          m.lock_reader();
          readers.fetch_add(1);
          assert(writers.load() == 0);
          assert(value >= 0 && value <= 6000);
          readers.fetch_sub(1);
          m.unlock_reader();
        } else {
          m.lock();
          assert(writers.fetch_add(1) == 0);
          assert(readers.load() == 0);
          value++;
          writers.fetch_sub(1);
          m.unlock();
        }
      }
    });
  }
  for (auto &worker : workers) worker.join();
  assert(value == 6000);
  std::cout << "shared readers, exclusive writers, and exact counts passed\n";
}
