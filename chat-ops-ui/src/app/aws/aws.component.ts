import { Component } from '@angular/core';
import { VMComponent } from "./../vm/vm.component";
import { AWSService } from "./aws.service";


@Component({
  selector: 'app-aws',
  templateUrl: './../vm/vm.component.html',
  styleUrls: ['./../vm/vm.component.css']
})
export class AWSComponent extends VMComponent {
  service = AWSService;
  constructor(vmService: AWSService) {
    super();
    this.vmService = vmService;
  }
}