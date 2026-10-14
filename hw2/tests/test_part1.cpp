#include <atomic>
#include <cassert>
#include <iostream>
#include <thread>
#include <vector>
#include TEST_HEADER

int main() {
  for (int threads : {1, 2, 4, 8}) {
    mutex m;
    m.init(threads);
    int count = 0;
    std::atomic<int> inside(0);
    std::vector<std::thread> workers;
    for (int id = 0; id < threads; id++) {
      workers.emplace_back([&, id]() {
        for (int i = 0; i < 2000; i++) {
          m.lock(id);
          assert(inside.fetch_add(1) == 0);
          count++;
          assert(inside.fetch_sub(1) == 1);
          m.unlock(id);
        }
      });
    }
    for (auto &worker : workers) worker.join();
    assert(count == threads * 2000);
  }
  std::cout << "mutual exclusion and exact counts passed\n";
}
