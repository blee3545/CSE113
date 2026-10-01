
#include <iostream>
#include <assert.h>
#include <chrono>
using namespace std;
using namespace std::chrono;


void reference_loop(float *b, int size) {
  for (int i = 0; i < size; i++) {
    float tmp = b[i];
    tmp += 1.0f;
    tmp += 2.0f;
    b[i] = tmp;
  }
}
void homework_loop_sequential(float *b, int size) {
for (int i=0; i<size;i+=2) {
float tmp0 = b[i +0];
tmp0 +=1.0f;
tmp0 +=2.0f;
b[i +0]=tmp0;
float tmp1 = b[i +1];
tmp1 +=1.0f;
tmp1 +=2.0f;
b[i +1]=tmp1;
}

}
void homework_loop_interleaved(float *b, int size) {
for (int i=0;i<size;i+= 2) {
float tmp0=b[i+0];
float tmp1=b[i+1];
tmp0+=1.0f;
tmp1+=1.0f;
tmp0+=2.0f;
tmp1+=2.0f;
b[i+0]=tmp0;
b[i+1]=tmp1;
}

}

#define CHAIN_LENGTH 2
#define UNROLL_FACTOR 2

#define SIZE 1024 * 1024 * 8

int main() {
  float *a;
  a = (float *) malloc(SIZE * sizeof(float));

  float *b;
  b = (float *) malloc(SIZE * sizeof(float));

  float *c;
  c = (float *) malloc(SIZE * sizeof(float));

  for (int i = 0; i < SIZE; i++) {
    a[i] = i;
    b[i] = i;
    c[i] = i;
  }

  auto sequential_start = high_resolution_clock::now();
  homework_loop_sequential(a,SIZE);
  auto sequential_end = high_resolution_clock::now();
  auto sequential_duration = duration_cast<nanoseconds>(sequential_end - sequential_start);
  double sequential_seconds = sequential_duration.count()/1000000000.0;

  auto interleaved_start = high_resolution_clock::now();
  homework_loop_interleaved(c,SIZE);
  auto interleaved_end = high_resolution_clock::now();
  auto interleaved_duration = duration_cast<nanoseconds>(interleaved_end - interleaved_start);
  double interleaved_seconds = interleaved_duration.count()/1000000000.0;

  auto ref_start = high_resolution_clock::now();
  reference_loop(b,SIZE);
  auto ref_stop = high_resolution_clock::now();
  auto ref_duration = duration_cast<nanoseconds>(ref_stop - ref_start);
  double ref_seconds = ref_duration.count()/1000000000.0;

  double seq_speedup = ref_seconds / sequential_seconds;
  double interleaved_speedup = ref_seconds / interleaved_seconds;
  cout << "sequential loop time: " << sequential_seconds << endl;
  cout << "interleaved loop time: " << interleaved_seconds << endl;
  cout << "reference loop time: " << ref_seconds << endl;
  cout << "----" << endl;
  cout << "speedups:" << endl;
  cout << "sequential speedup over reference: " << seq_speedup << endl << endl;
  cout << "interleaved speedup over reference: " << interleaved_speedup << endl << endl;

  return 0;
}
