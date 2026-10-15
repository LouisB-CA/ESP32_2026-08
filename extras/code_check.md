

# Checklist of Embedded C++ Best Practices

### 1. Header files should compile by themselves
```bash
for HDR in src/*.h ; do
    g++ -Wall -Wextra -Wpedantic -std=c++17 $HDR
done
```

### 2.  A source file's own header should be included first
* The first `#include` in a.cpp file should be a.h
* Additional headers may be included in any order

