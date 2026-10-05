#include <thread>
#include <vector>
using namespace std;

/** You may add additional functions as needed in this file. */

void round_robin_worker(volatile int *b, int size, int k, int tid, int num_threads) {
  for (int i = tid; i < size; i += num_threads) {
    for (int count = 0; count < k; count++) {
      b[i]++;
    }
  }
}

void contiguous_worker(volatile int *c, int start, int end, int k) {
  for (int i = start; i < end; i++) {
    for (int count = 0; count < k; count++) {
      c[i]++;
    }
  }
}

/** Write your sequential computation here. */
void sequential_increment(volatile int *a, int size, int k) {
  for (int i = 0; i < size; i++) {
    for (int count = 0; count < k; count++) {
      a[i]++;
    }
  }
}

/** Write your round robin computation here.*/
void round_robin_increment(volatile int *b, int size, int k, int num_threads) {
  vector<thread> threads;

  for (int tid = 0; tid < num_threads; tid++) {
    threads.emplace_back(round_robin_worker, b, size, k, tid, num_threads);
  }

  for (thread &worker : threads) {
    worker.join();
  }
}

/** Write your custom computation here. */
void custom_increment(volatile int *c, int size, int k, int num_threads) {
  vector<thread> threads;

  for (int tid = 0; tid < num_threads; tid++) {
    int start = tid * size / num_threads;
    int end = (tid + 1) * size / num_threads;
    threads.emplace_back(contiguous_worker, c, start, end, k);
  }

  for (thread &worker : threads) {
    worker.join();
  }
}
