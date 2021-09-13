import { useState } from 'preact/hooks';
import Router from 'preact-router';
import { createHashHistory } from 'history';
import html from 'html';
import DbDropdown from './dbdropdown.js';
import Cards from './cards.js';
import CardNew from './cardnew.js';

const App = ({ metabaseUrl, webPath }) => {
  let [cards, setCards] = useState(null);
  const addCard = (card) => setCards((cards || []).concat([card]));
  const updateCard = (id, card) => setCards(cards.map(c => c.id == id ? { ...c, ...card } : c));
  const removeCard = (id) => setCards(cards.filter(c => c.id != id));

  let [dbs, setDbs] = useState(null);

  const api = `${window.location.protocol}//${window.location.host}${webPath}api/`;

  return html`
    <div id="app">
      <nav className="navbar navbar-expand-md navbar-light bg-light">
        <div className="container">
          <a className="navbar-brand" href="/">Metabase Matview</a>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <div className="navbar-nav me-auto mb-2 mb-lg-0">
              <${DbDropdown} className="nav-item" ...${{ dbs, setDbs, api }} />
              <div className="nav-item">
                <a className="nav-link btn btn-default" href="/new">Add question</a>
              </div>
            </div>
            <div className="navbar-nav">
              <a className="nav-link btn btn-default" href="${metabaseUrl}">
                Go to Metabase
                <span className="fa fa-external-link ps-2" />
              </a>
            </div>
          </div>
        </div>
      </nav>
      <div className="container">
        <${Router} history=${createHashHistory()}>
          <p path="/"><em>Select a database...</em></p>
          <${Cards} path="/database/:dbId" ...${{ cards, setCards, updateCard, removeCard, metabaseUrl, api }} />
          <${CardNew} path="/new" ...${{ addCard, api }} />
        </${Router}>
      </div>
    </div>
  `;
}

export default App;
