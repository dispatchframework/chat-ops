import { Component } from '@angular/core';
import { VMComponent } from "../vm/vm.component";
import { VMwareService } from "./vmware.service";


@Component({
  selector: 'app-vmware',
  templateUrl: './../vm/vm.component.html',
  styleUrls: ['./../vm/vm.component.css']
})
export class VMwareComponent extends VMComponent {
  service = VMwareService;
  constructor(vmService: VMwareService) {
    super();
    this.vmService = vmService;
  }
}