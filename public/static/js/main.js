document.querySelectorAll('[data-vote]').forEach(widget => {
    const output = widget.querySelector('output');
    const buttons = [...widget.querySelectorAll('button')];
    const original = Number(output.value) - Number(widget.dataset.selected || 0);

    buttons.forEach(button => button.addEventListener('click', () => {
        const selected = button.getAttribute('aria-pressed') === 'true'
            ? 0 : Number(button.dataset.value);
        widget.dataset.selected = selected;
        buttons.forEach(item => {
            item.setAttribute('aria-pressed', String(Number(item.dataset.value) === selected));
        });
        output.value = original + selected;
    }));
});

// Одновременно может быть выбран один правильный ответ.
document.querySelectorAll('[data-correct]').forEach(box => {
    box.addEventListener('change', () => {
        document.querySelectorAll('[data-correct]').forEach(other => {
            if (other !== box) other.checked = false;
        });
    });
});
