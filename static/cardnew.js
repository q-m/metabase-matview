import html from 'html';
import { route } from 'preact-router';

const CardNew = ({ addCard, api }) => (
  html`
    <form onSubmit=${e => onSubmit(e, addCard, api)}>
      <div className="mb-3">
        <label for="new_card_id" className="form-label">Metabase question ID</label>
        <input type="text" className="form-control" id="new_card_id" style="width: 5em" />
      </div>
      <a className="btn btn-default" href="/">Back</button>
      <button type="submit" className="btn btn-primary" id="new_card_submit">Materialize question</button>
    </form>
  `
);

function onSubmit(e, addCard, api) {
  e.preventDefault();

  const submit = document.getElementById('new_card_submit');
  submit.classList.add('disabled');

  const id = parseInt(document.getElementById('new_card_id').value);
  fetch(`${api}1/card/${id}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => addCard(data))
    .then(() => route('/'))
    .finally(data => submit.classList.remove('disabled'));
}

export default CardNew;
