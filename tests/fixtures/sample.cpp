#include <cmath>

static const double PI = 3.14159;

struct Point { double x, y; };

double dist(Point a, Point b) {
    return std::sqrt((a.x-b.x)*(a.x-b.x) + (a.y-b.y)*(a.y-b.y));
}

// trailing comment
