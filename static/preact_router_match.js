// https://github.com/preactjs/preact-router/blob/3.2.1/src/match.js
// included here because ES6 Module import doesn't work :(
import { h, Component } from 'preact';
import { subscribers, getCurrentUrl, Link as StaticLink, exec } from 'preact-router';

export class Match extends Component {
	update = url => {
		this.nextUrl = url;
		this.setState({});
	};
	componentDidMount() {
		subscribers.push(this.update);
	}
	componentWillUnmount() {
		subscribers.splice(subscribers.indexOf(this.update)>>>0, 1);
	}
	render(props) {
		let url = this.nextUrl || getCurrentUrl(),
			path = url.replace(/\?.+$/,'');
		this.nextUrl = null;
		return props.children({
			url,
			path,
			matches: exec(path, props.path, {}) !== false
		});
	}
}

export default Match;