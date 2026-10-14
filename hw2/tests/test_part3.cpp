#include <atomic>
#include <cassert>
#include <iostream>
#include <thread>
#include <vector>
#include TEST_HEADER

int main() {
  CSE113_Stack s;
  assert(s.peek() == -1 && s.pop() == -1);
#ifdef TEST_SWAPTOP
  s.swaptop(2);
  assert(s.peek() == -1);
#endif
  for (int value = 0; value <= 2; value++) s.push(value);
  assert(s.pop() == 2 && s.peek() == 1);
#ifdef TEST_SWAPTOP
  for (int value : {0, 1, 2, 2}) {
    s.swaptop(value);
    assert(s.peek() == value);
  }
  s.swaptop(1);
#endif
  assert(s.pop() == 1 && s.pop() == 0 && s.pop() == -1);

  // Concurrent pushes must preserve every node, using only legal values.
  std::vector<std::thread> workers;
  for (int id = 0; id < 6; id++) {
    workers.emplace_back([&, id]() {
      for (int i = 0; i < 100; i++) s.push(id % 3);
    });
  }
  for (auto &worker : workers) worker.join();
  int counts[3] = {0, 0, 0};
  workers.clear();
  std::atomic<int> popped[3];
  for (auto &count : popped) count.store(0);
  for (int id = 0; id < 6; id++) {
    workers.emplace_back([&]() {
      while (true) {
        int value = s.pop();
        if (value == -1) break;
        assert(value >= 0 && value <= 2);
        popped[value].fetch_add(1);
      }
    });
  }
  for (auto &worker : workers) worker.join();
  for (int i = 0; i < 3; i++) {
    counts[i] = popped[i].load();
    assert(counts[i] == 200);
  }

  workers.clear();
  for (int id = 0; id < 8; id++) {
    workers.emplace_back([&, id]() {
      for (int i = 0; i < 1000; i++) {
        int value = -1;
        if (id < 2) s.push(i % 3);
        else if (id < 4) value = s.pop();
#ifdef TEST_SWAPTOP
        else if (id < 6) s.swaptop(i % 3);
#endif
        else value = s.peek();
        assert(value >= -1 && value <= 2);
      }
    });
  }
  for (auto &worker : workers) worker.join();
  while (s.pop() != -1) {}
  std::cout << "LIFO, empty cases, node counts, and concurrent operations passed\n";
}
