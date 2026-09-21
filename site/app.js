const commands = {
  replay: "python3 -m jev replay --fixture examples/fixtures/fresh-100 --out results/fresh",
  gate: "python3 -m jev ask --state examples/ask/gate-state.json --questions agent_action_gate_v1 --mock-responses examples/ask/gate-mock-response.json --out results/gate",
  tests: "python3 -m unittest discover -s tests -v"
};

const header = document.querySelector("[data-header]");
const nav = document.querySelector("[data-nav]");
const navToggle = document.querySelector("[data-nav-toggle]");
const output = document.querySelector("[data-command-output]");

window.addEventListener("scroll", () => header.classList.toggle("scrolled", window.scrollY > 20), { passive: true });

navToggle.addEventListener("click", () => {
  const open = nav.classList.toggle("open");
  navToggle.setAttribute("aria-expanded", String(open));
});

nav.addEventListener("click", event => {
  if (event.target.matches("a")) {
    nav.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
  }
});

document.querySelectorAll("[data-command]").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-command]").forEach(item => {
      const active = item === button;
      item.classList.toggle("active", active);
      item.setAttribute("aria-selected", String(active));
    });
    output.textContent = commands[button.dataset.command];
  });
});

document.querySelector("[data-copy]").addEventListener("click", async event => {
  await navigator.clipboard.writeText(output.textContent);
  const button = event.currentTarget;
  button.textContent = "Copied";
  window.setTimeout(() => { button.textContent = "Copy"; }, 1400);
});

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll(".reveal").forEach(element => observer.observe(element));
