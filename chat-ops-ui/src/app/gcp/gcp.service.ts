import { Injectable } from '@angular/core';

import { VMService } from '../vm/vm.service';

@Injectable({
  providedIn: 'root'
})
export class GCPService extends VMService {
  cloud = "gcp";
}
