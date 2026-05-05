function myFunction(x) {
    if (getComputedStyle(x).display === "none") {
        x.style.display = "block";
      } else {
        x.style.display = "none";
      }
    }