async function sendForm(url, data) {
    const token = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const response = await fetch(url, {
        method: 'POST',
        headers: {'X-CSRFToken': token},
        body: new URLSearchParams(data),
        credentials: 'same-origin'
    });
    const type = response.headers.get('content-type') || '';
    const result = type.includes('application/json') ? await response.json() : null;
    if (!response.ok) {
        throw new Error(result?.message || 'Ошибка запроса: ' + response.status);
    }
    return result;
}

document.querySelectorAll('[data-vote]').forEach(widget => {
    const buttons = widget.querySelectorAll('button');
    buttons.forEach(button => button.addEventListener('click', async () => {
        buttons.forEach(item => item.disabled = true);
        try {
            const result = await sendForm(widget.dataset.url, {value: button.dataset.value});
            widget.querySelector('output').value = result.rating;
            buttons.forEach(item => item.setAttribute('aria-pressed', String(Number(item.dataset.value) === result.selected)));
        } catch (error) {
            alert(error.message);
        } finally {
            buttons.forEach(item => item.disabled = false);
        }
    }));
});

document.querySelectorAll('[data-correct]').forEach(box => {
    box.addEventListener('change', async () => {
        const previous = !box.checked;
        box.disabled = true;
        try {
            const result = await sendForm(box.dataset.url, {question: box.dataset.question, answer: box.dataset.answer, correct: box.checked ? '1' : '0'});
            document.querySelectorAll('[data-correct]').forEach(item => item.checked = Number(item.dataset.answer) === result.answer_id);
        } catch (error) {
            box.checked = previous;
            alert(error.message);
        } finally {
            box.disabled = false;
        }
    });
});
