import html from 'html';
import { useEffect } from 'preact/hooks';

const Cards = ({ dbId, cards, setCards, updateCard, removeCard, api, metabaseUrl }) => {
  dbId = parseInt(dbId); // against URL hacks

  useEffect(() => {
    fetch(`${api}1/database/${dbId}/cards`)
      .then(res => res.json())
      .then(data => setCards(data));
  }, []);

  if (cards && cards.length > 0) {
    return html`
      <ul className="list-group mt-3">
        ${cards.map(card => (
          html`
            <li className="list-group-item d-flex align-items-baseline">
              <div style="width: 5.5em" className="text-muted pe-1">
                #${card.id}
              </div>
              <div className="flex-fill">
                <a href="${metabaseUrl}question/${card.id}" className="btn btn-outline">
                  ${card.name}
                  <span className="fa fa-external-link ps-2" />
                </a>
                <small className="text-muted ms-3">${card.view_refreshed_at}</small>
              </div>
              <div>
                <a href="#" className="btn btn-sm btn-primary me-1" onClick=${e => onRefresh(e, card.id, api, updateCard)}>Refresh</a>
                <a href="#" className="btn btn-sm btn-warning" onClick=${e => onDelete(e, card.id, api, removeCard)}>Unmaterialize</a>
              </div>
            </li>
          `
        ))}
      </ul>
    `;

  } else if (cards && cards.length == 0) {
    return html`
      <div className="alert alert-light">
        <em>No materialized questions found, start by adding one.</em>
      </div>
    `;

  } else {
    return html`
      <div className="alert alert-light">
        <em>Loading...</em>
      </div>
    `;
  }
}

function onRefresh(e, id, api, updateCard) {
  e.preventDefault();
  e.target.classList.add('disabled');
  fetch(`${api}1/card/${id}/refresh`, { method: 'POST' })
    .then(res => res.json())
    .then(data => updateCard(id, data))
    .finally(data => e.target.classList.remove('disabled'));
}

function onDelete(e, id, api, removeCard) {
  e.preventDefault();
  e.target.classList.add('disabled');
  fetch(`${api}1/card/${id}`, { method: 'DELETE' })
    .then(res => res.json())
    .then(data => removeCard(id))
    .finally(data => e.target.classList.remove('disabled'));
}

export default Cards;
