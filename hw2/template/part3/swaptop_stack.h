#pragma once
#include <mutex>
#include <shared_mutex>
using namespace std;

class Llist_node {
 public:  
  Llist_node(int d) {   
    data = d;
    next = NULL;
  }
  
  int data;
  Llist_node *next;
};

class CSE113_Stack {
 public:
  
  CSE113_Stack() {
    start = NULL;
  }
  
  int pop() {
    unique_lock<shared_mutex> guard(stack_mutex);
    if (start == NULL) {
      return -1;
    }

    if (start->next == NULL) {
      int ret = start->data;
      delete start;
      start = NULL;
      return ret;
    }

    Llist_node *current = start->next;
    Llist_node *previous = start;
    while (current->next != NULL) {
      previous = current;
      current = current->next;
    }

    int ret = current->data;
    previous->next = NULL;
    delete current;
    return ret;
  }

  
  int peek() {
    shared_lock<shared_mutex> guard(stack_mutex);
    if (start == NULL) {
      return -1;
    }
    
    Llist_node *current = start;
    while (current->next != NULL) {
      current = current->next;
    }
    return current->data;    
  }
  
  void push(int p) {
    unique_lock<shared_mutex> guard(stack_mutex);
    if (start == NULL) {

      start = new Llist_node(p);
      return;
    }

    Llist_node *current = start;
    while (current->next != NULL) {
      current = current->next;
    }

    current->next = new Llist_node(p);
  }

  void swaptop(int to_swap) {
    {
      shared_lock<shared_mutex> guard(stack_mutex);
      if (start == NULL) {
        return;
      }
      Llist_node *current = start;
      while (current->next != NULL) {
        current = current->next;
      }
      // With only three possible values, replacing a value with itself
      // is common. This case only needs a reader lock.
      if (current->data == to_swap) {
        return;
      }
    }

    // A shared lock cannot be upgraded directly. After releasing it,
    // another thread may change/remove the tail, so traverse again.
    unique_lock<shared_mutex> guard(stack_mutex);
    if (start == NULL) {
      return;
    }
    Llist_node *current = start;
    while (current->next != NULL) {
      current = current->next;
    }
    current->data = to_swap;
  }

 private:
  shared_mutex stack_mutex;
  Llist_node *start;  
};
