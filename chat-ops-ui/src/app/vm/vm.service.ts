import { Injectable } from '@angular/core';
import { Http, Response, RequestOptions, Headers }  from '@angular/http';
import { Observable }                               from 'rxjs/Observable';
import { environment }                              from '../../environments/environment';
import { interval, throwError } from 'rxjs';

import 'rxjs/add/operator/map';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/switchMap';

import { VM } from '../vm/vm';

@Injectable({
  providedIn: 'root'
})
export abstract class VMService {

  cloud !: string;

  private schedule = interval(5000)

  constructor(private http: Http) { }

  _requestOptions(): RequestOptions {
    let headers = new Headers();
    headers.append("accept", "application/json");
    headers.append("content-type", "application/json");
    return new RequestOptions({ headers: headers });
  }

  getVMs(): Observable<VM[]> {
    let t = this;
    return this.http.get(environment.apiURL + this.cloud + '?command=list', this._requestOptions())
      .map(function(res: Response){return t.extractVMs(t.cloud, res);})
      .catch(this.handleError);
  }

  deleteVM(vm: VM) {
    return this.http.get(
      environment.apiURL + this.cloud + '?command=delete&name=' + vm.name, this._requestOptions())
      .catch(this.handleError);
  }

  refreshVMs(period: number): Observable<VM[]> {
    let t = this;
    return this.schedule
      .switchMap(() => this.http.get(environment.apiURL + this.cloud + '?command=list', this._requestOptions()))
      .map(function(res: Response){return t.extractVMs(t.cloud, res);})
      .catch(this.handleError);
  }

  extractVMs(cloud: string, res: Response) {
    let data = res.json();
    if (data) {
      data.forEach(element => {
        element.cloud = cloud
        element.name = element.name
        element.id = element.id
        element.state = element.status
      });
      console.log(data);
      return data;
    }
    return { };
  }

  private handleError (error: Response | any) {
    // In a real world app, you might use a remote logging infrastructure
    let errMsg: string;
    if (error instanceof Response) {
      const body = error.json() || '';
      const err = body.error || JSON.stringify(body);
      errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
    } else {
      errMsg = error.message ? error.message : error.toString();
    }
    console.error(errMsg);
    return throwError(errMsg);
  }
}
