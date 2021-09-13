import html from 'html';
import { useEffect } from 'preact/hooks';

const DbDropdown = ({ api, dbs, setDbs, selectedDbId, className }) => {
  useEffect(() => {
    fetch(`${api}1/databases`)
      .then(res => res.json())
      .then(data => setDbs(data));
  }, []);

  const selectedDb = (dbs || []).find(db => db.id === selectedDbId);

  return html`
    <div className=${`dropdown ${className}`}>
      <a class="nav-link dropdown-toggle" href="#" id="dbDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
        ${selectedDb ? selectedDb.name : html`<em>Select database...</em>`}
      </a>
      <ul className="dropdown-menu" aria-labelledby="dbDropdown">
        ${(dbs || []).map(db => (
          html`<li><a className="dropdown-item" href="/database/${db.id}">${db.name}</a></li>`
        ))}
        ${!!dbs && dbs.length == 0 && (
          html`<li><a className="dropdown-item disabled" href="#"><em>No databases configured.</em></a></li>`
        )}
        ${!dbs && (
          html`<li><a className="dropdown-item disabled" href="#"><em>Loading...</em></a></li>`
        )}
      </ul>
    </div>
  `;
}

export default DbDropdown;
