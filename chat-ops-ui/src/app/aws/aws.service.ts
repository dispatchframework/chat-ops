import { Injectable } from '@angular/core';

import { VMService } from '../vm/vm.service';

@Injectable({
  providedIn: 'root'
})
export class AWSService extends VMService {
  cloud = "aws";
}
